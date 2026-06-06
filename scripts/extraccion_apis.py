import finnhub
import feedparser
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv() 
# ==========================================
# CONFIGURACIÓN DE CONEXIONES
# ==========================================
API_KEY = os.getenv("FINNHUB_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not API_KEY or not MONGO_URI:
    print("❌ ERROR: Faltan credenciales (FINNHUB_API_KEY o MONGO_URI) en el archivo .env")
    exit()

# Conexión a MongoDB (Base de datos HedgeMind)
client = MongoClient(MONGO_URI)
db = client['hedgemind_db']

# Definición de las 3 colecciones
col_finnhub = db['finnhubNVDA']
col_google = db['googleNVDA']
col_kaggle = db['kaggleNVDA']

# Limpiar las colecciones antes de la nueva ingesta
col_finnhub.drop()
col_google.drop()
col_kaggle.drop()
print("🧹 Colecciones ('finnhubNVDA', 'googleNVDA', 'kaggleNVDA') limpiadas para nueva ingesta.")

finnhub_client = finnhub.Client(api_key=API_KEY)
ticker = "NVDA"

print("🚀 INICIANDO INGESTA HACIA MONGODB DATA LAKE...")

# ==========================================
# 1. FINNHUB -> Colección: finnhubNVDA
# ==========================================
def extraer_finnhub(ticker, meses_atras=12):
    print(f"📥 [FINNHUB] Descargando noticias de {ticker}...")
    todas_las_noticias = []
    fecha_actual = datetime.now()
    
    for _ in range(meses_atras):
        fecha_inicio_bloque = fecha_actual - timedelta(days=30)
        str_inicio = fecha_inicio_bloque.strftime('%Y-%m-%d')
        str_fin = fecha_actual.strftime('%Y-%m-%d')
        
        try:
            bloque = finnhub_client.company_news(ticker, _from=str_inicio, to=str_fin)
            todas_las_noticias.extend(bloque)
            time.sleep(1) 
        except Exception as e:
            print(f"   ⚠️ Error bloque {str_inicio}: {e}")
        fecha_actual = fecha_inicio_bloque
    return todas_las_noticias

noticias_finnhub = extraer_finnhub(ticker)
if noticias_finnhub:
    df_f = pd.DataFrame(noticias_finnhub)
    df_f['date'] = pd.to_datetime(df_f['datetime'], unit='s').dt.strftime('%Y-%m-%d')
    df_f = df_f.rename(columns={'headline': 'title', 'summary': 'content'})
    df_f['origen_dato'] = 'Finnhub_API'
    
    # Seleccionar columnas y enviar a la colección específica
    records_f = df_f[['date', 'title', 'content', 'source', 'url', 'origen_dato']].to_dict("records")
    col_finnhub.insert_many(records_f)
    print(f"✅ [FINNHUB] {len(records_f)} documentos inyectados en la colección 'finnhubNVDA'.")

# ==========================================
# 2. GOOGLE NEWS -> Colección: googleNVDA
# ==========================================
def extraer_google_news(ticker):
    print(f"📥 [GOOGLE NEWS] Descargando titulares de {ticker}...")
    url = f"https://news.google.com/rss/search?q={ticker}&hl=es&gl=ES&ceid=ES:es"
    feed = feedparser.parse(url)
    
    noticias = []
    for entry in feed.entries:
        noticias.append({
            'date': datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d'),
            'title': entry.title,
            'content': '', 
            'source': entry.source.title if hasattr(entry, 'source') else 'Google News',
            'url': entry.link,
            'origen_dato': 'Google_News'
        })
    return noticias

noticias_google = extraer_google_news(ticker)
if noticias_google:
    col_google.insert_many(noticias_google)
    print(f"✅ [GOOGLE NEWS] {len(noticias_google)} documentos inyectados en la colección 'googleNVDA'.")

# ==========================================
# 3. KAGGLE -> Colección: kaggleNVDA
# ==========================================
print("📥 [KAGGLE] Leyendo dataset histórico...")
ruta_kaggle = "../datasets/noticiaskaggle.csv" 

if os.path.exists(ruta_kaggle):
    df_k = pd.read_csv(ruta_kaggle, on_bad_lines='skip')
    
    # Estandarización mínima
    if 'headline' in df_k.columns:
        df_k = df_k.rename(columns={'headline': 'title'})
        
    df_k['content'] = '' 
    df_k['origen_dato'] = 'Kaggle_Dataset'
    
    cols_necesarias = ['date', 'title', 'origen_dato']
    if all(col in df_k.columns for col in cols_necesarias):
        df_k = df_k[cols_necesarias]
        
        # --- EL SALVACAÍDAS DE LA CUOTA: FILTRADO SECTORIAL ---
        print(f"   🔍 Dataset original: {len(df_k)} filas. Filtrando por sector...")
        keywords = ['nvda', 'nvidia', 'semiconductor', 'chip', 'amd', 'intel', 'tsmc', 'gpu', 'ai']
        pattern = '|'.join([f"\\b{kw}\\b" for kw in keywords])
        df_k = df_k[df_k['title'].str.contains(pattern, case=False, na=False)].copy()
        print(f"Tras el filtro: {len(df_k)} noticias relevantes para subir.")
        # -----------------------------------------------------

        # Parseo seguro de fechas para Kaggle
        df_k['date'] = pd.to_datetime(df_k['date'], format='mixed', errors='coerce', utc=True)
        df_k = df_k.dropna(subset=['date', 'title']) 
        df_k['date'] = df_k['date'].dt.strftime('%Y-%m-%d')
        
        records_k = df_k.to_dict("records")
        if records_k:
            col_kaggle.insert_many(records_k)
            print(f"✅ [KAGGLE] {len(records_k)} documentos inyectados en la colección 'kaggleNVDA'.")
    else:
        print("⚠️ [KAGGLE] El CSV no tiene las columnas necesarias (date, title).")
else:
    print(f"⚠️ [KAGGLE] Archivo no encontrado en {ruta_kaggle}")

# ==========================================
# RESUMEN FINAL
# ==========================================
print("\n" + "="*50)
print(f"🎉 INGESTA A HEDGEMIND_DB COMPLETADA EXITOSAMENTE")
print(f"🗄️ Documentos en 'finnhubNVDA': {col_finnhub.count_documents({})}")
print(f"🗄️ Documentos en 'googleNVDA':  {col_google.count_documents({})}")
print(f"🗄️ Documentos en 'kaggleNVDA':  {col_kaggle.count_documents({})}")
print("="*50)