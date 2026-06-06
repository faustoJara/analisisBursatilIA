from pymongo import MongoClient
import os 
from dotenv import load_dotenv

load_dotenv()

# Tu URI extraída de tu configuración
uri = os.getenv("MONGO_URI")

try:
    client = MongoClient(uri)
    # Probar conexión listando las bases de datos
    db = client.test_database
    print("✅ ¡Conexión a MongoDB Atlas exitosa!")
    print(f"Bases de datos disponibles: {client.list_database_names()}")
    
    # Insertar un documento de prueba para verificar permisos
    db.noticias_test.insert_one({"noticia": "NVIDIA sube gracias a la IA", "fecha": "2026-05-31"})
    print("✅ Escritura de prueba realizada correctamente.")
    
except Exception as e:
    print(f"❌ Error al conectar a MongoDB: {e}")