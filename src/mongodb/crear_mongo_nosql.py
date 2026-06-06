import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

def configurar_mongodb():
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    
    if not uri:
        print("❌ Error: MONGO_URI no encontrada en el archivo .env")
        return

    print("🔌 Conectando al clúster de MongoDB Atlas...")
    # maxPoolSize ayuda a gestionar múltiples peticiones si usamos Apache NiFi luego
    cliente = MongoClient(uri, maxPoolSize=50, serverSelectionTimeoutMS=5000)

    try:
        # Validación estricta de credenciales
        cliente.admin.command('ping')
        print("✅ Ping exitoso: Conexión establecida con la nube de MongoDB.")
    except Exception as e:
        print(f"❌ Error de conexión. Revisa tu IP y credenciales: {e}")
        return

    # 1. Definimos la Base de Datos y Colección para nuestro TFM
    nombre_db = "nvda"
    nombre_coleccion = "financial_news"
    
    db = cliente[nombre_db]
    coleccion = db[nombre_coleccion]

    # 2. Documento Semilla (Fuerza la creación de la arquitectura en Atlas)
    # Este es el formato exacto que recibiremos luego de la API de noticias
    noticia_semilla = {
        "ticker": "NVDA",
        "fuente": "Script_Inicializacion",
        "fecha_ingesta": datetime.utcnow(),
        "titular": "Inicialización de la base de datos de noticias financieras completada",
        "sentiment_score": 0.0, # Valor neutral de inicialización
        "procesado": True
    }

    print(f"⚙️ Insertando documento semilla para inicializar la base de datos '{nombre_db}'...")
    resultado = coleccion.insert_one(noticia_semilla)
    
    print(f"✅ Documento insertado con éxito. ID: {resultado.inserted_id}")
    print("📁 Colección 'financial_news' lista para recibir datos de Apache NiFi / Kafka.")
    
    cliente.close()

if __name__ == "__main__":
    configurar_mongodb()