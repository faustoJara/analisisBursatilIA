import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ==============================================================================
# 1. LECTURA DEL DATASET LOCAL
# ==============================================================================
print("📖 Cargando el archivo CSV en memoria desde el disco local...")
# Lee directamente el archivo que has descargado y guardado en tu carpeta
try:
    df_news_raw = pd.read_csv("datasetnews/raw_analyst_ratings.csv", on_bad_lines='skip') 
    print(f"✅ Dataset cargado con éxito. Filas totales: {len(df_news_raw)}")
except FileNotFoundError:
    print("❌ ERROR: No se encuentra el archivo 'raw_analyst_ratings.csv'. Asegúrate de que está en la misma carpeta que este script.")
    exit()

# ==============================================================================
# 2. FILTRADO Y ANÁLISIS DE LENGUAJE NATURAL (NLP)
# ==============================================================================
print("🔍 Filtrando exclusivamente noticias de NVIDIA (NVDA)...")
df_nvda_news = df_news_raw[df_news_raw['stock'] == 'NVDA'].copy()

# Limpieza de fechas
df_nvda_news['date'] = pd.to_datetime(df_nvda_news['date'], errors='coerce').dt.tz_localize(None).dt.floor('D')
df_nvda_news.dropna(subset=['date', 'headline'], inplace=True)

print(f"📰 Noticias de NVIDIA encontradas: {len(df_nvda_news)}")
print("🧠 Aplicando modelo de Procesamiento de Lenguaje Natural (VADER)...")

analyzer = SentimentIntensityAnalyzer()

# Calculamos el sentimiento de cada titular (Compound: -1 muy negativo, +1 muy positivo)
df_nvda_news['sentiment_score'] = df_nvda_news['headline'].apply(lambda txt: analyzer.polarity_scores(txt)['compound'])

# Agrupamos por día: calculamos la media del sentimiento y contamos el volumen de noticias
df_news_diario = df_nvda_news.groupby('date').agg(
    real_sentiment_score=('sentiment_score', 'mean'),
    real_news_volume=('headline', 'count')
)

# ==============================================================================
# 3. CONEXIÓN A AWS RDS Y ACTUALIZACIÓN (MERGE)
# ==============================================================================
print("☁️ Conectando a Amazon RDS para integrar los datos reales...")
load_dotenv()
conexion_str = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(conexion_str)

# Descargamos la tabla que ya tienes en AWS (con el mercado de YFinance)
df_aws = pd.read_sql("SELECT * FROM dataset_nvda_unificado", con=engine, index_col='fecha')
df_aws.index = pd.to_datetime(df_aws.index)

# Cruzamos los datos del mercado con las noticias reales
df_final = df_aws.merge(df_news_diario, left_index=True, right_index=True, how='left')

# Sustituimos las columnas simuladas por las reales
df_final['sentiment_score'] = df_final['real_sentiment_score'].fillna(0) # Neutro si no hay noticias
df_final['news_volume'] = df_final['real_news_volume'].fillna(0) # 0 noticias

# Borramos las columnas temporales
df_final.drop(columns=['real_sentiment_score', 'real_news_volume'], inplace=True)

# Guardamos la tabla definitiva 100% REAL de vuelta en Amazon AWS
print("💾 Sobrescribiendo la base de datos en Amazon RDS con el dataset definitivo...")
df_final.to_sql('dataset_nvda_unificado', con=engine, if_exists='replace', index=True, index_label='fecha')

