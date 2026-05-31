import json
import redis
from kafka import KafkaConsumer
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
# Iniciamos las conexiones
mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client['TV_StreamDB']
col_noticias = mongo_db['noticias_raw']

# MariaDB / RDS
db_sql = mysql.connector.connect(
    host=os.getenv("DB_HOST"), # O tu endpoint de AWS
    user=os.getenv("DB_USER"), # El usuario que configuraste en tu RDS
    password=os.getenv("DB_PASSWORD"), # La contraseña que configuraste en tu RDS
    database="tfm_db"
)
cursor_sql = db_sql.cursor()

print("🔌 Iniciando motores de Streaming...")

# 1. Conexión a Redis (Caché local)
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
print("✅ Conectado a Redis.")

# 2. IA de Sentimiento
analyzer = SentimentIntensityAnalyzer()
print("🧠 Modelo VADER cargado.")

# 3. Conexión a Kafka
print("🎧 Escuchando el canal 'noticias_mercado' de Kafka...")
consumer = KafkaConsumer(
    'noticias_mercado',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest', # leer desde el principio del stream
    enable_auto_commit=True,
    group_id='hedgemind-group-1'
)
print("🎧 Escuchando... (Esperando eventos en tiempo real)")

# 4. El Bucle Infinito (Procesamiento en Tiempo Real)
for mensaje in consumer:
    try:
        # El RSS viene en formato XML, BeautifulSoup nos ayuda a extraer solo el texto
        xml_crudo = mensaje.value.decode('utf-8')
        sopa = BeautifulSoup(xml_crudo, 'xml')
        
        # Extraemos los titulares (etiqueta <title> en RSS)
        titulares = sopa.find_all('title')
        
        if titulares:
            print("\n" + "="*50)
            print(f"📰 ¡NUEVO BOLETÍN DETECTADO! ({len(titulares)} titulares)")
            
            sentimiento_total = 0
            
            for t in titulares[1:6]: # Leemos los 5 primeros titulares
                texto = t.get_text()
                score = analyzer.polarity_scores(texto)['compound']
                sentimiento_total += score
                print(f"   -> {texto[:60]}... [Score: {score}]")
                
            # Calculamos la media del sentimiento del boletín
            media_sentimiento = sentimiento_total / 5
            
            # 1. MongoDB: Guardamos datos en crudo
            col_noticias.insert_one({"xml_raw": xml_crudo, "timestamp": datetime.now()})

            # 2. SQL: Guardamos datos para el entrenamiento (Hito 3)
            sql = "INSERT INTO nvidia_historico (fecha, sentimiento, volumen_noticias) VALUES (%s, %s, %s)"
            cursor_sql.execute(sql, (datetime.now().strftime('%Y-%m-%d'), media_sentimiento, len(titulares)))
            db_sql.commit()
                        
            
            # 5. Guardar en Redis para que el XGBoost lo lea instantáneamente
            cache.set('nvda_current_sentiment', media_sentimiento)
            print(f"💾 Guardado en Redis | Sentimiento Global: {media_sentimiento:.4f}")
            print("="*50)

    except Exception as e:
        print(f"⚠️ Error procesando el mensaje: {e}")