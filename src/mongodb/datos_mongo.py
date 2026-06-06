import pymongo
import pandas as pd
from pprint import pprint
import os
from dotenv import load_dotenv

load_dotenv() # Asegúrate de que la ruta al .env es correcta

# 1. Conexión a MongoDB
URI = os.getenv("MONGO_URI")
cliente = pymongo.MongoClient(URI)
db = cliente["hedgemind_db"]


# 2. Lista de colecciones que queremos auditar
# (He omitido sentimiento_crudo temporalmente si no la estás llenando aún, 
# pero puedes añadirla a la lista si la necesitas)
colecciones_a_revisar = ["sentimiento_crudo","finnhubNVDA", "googleNVDA", "kaggleNVDA"]

print("=== 🔍 AUDITORÍA DEL DATA LAKE EN MONGODB ===\n")

# 3. Extraer y mostrar los últimos 5 mensajes de cada colección
for nombre_col in colecciones_a_revisar:
    coleccion = db[nombre_col]
    total_docs = coleccion.count_documents({})
    
    print(f"📦 COLECCIÓN: {nombre_col} | Total de documentos: {total_docs}")
    print("=" * 70)
    
    # Extraemos los últimos 5 documentos insertados
    documentos = list(coleccion.find().sort("_id", -1).limit(1))
    
    if not documentos:
        print("⚠️ La colección está vacía.")
    else:
        for doc in documentos:
            # Eliminamos el _id de la impresión visual para que quede más limpio en la captura
            doc_display = {k: v for k, v in doc.items() if k != '_id'}
            pprint(doc_display, sort_dicts=False)
            print("-" * 50)
    print("\n")

# =====================================================================
# OPCIONAL: VISTA EN DATAFRAME (Ideal si lo ejecutas en un Notebook)
# =====================================================================
# Descomenta esto en Jupyter para ver una de las colecciones como tabla:
# df_finnhub = pd.DataFrame(list(db["finnhubNVDA"].find().sort("_id", -1).limit(5)))
# display(df_finnhub.drop(columns=['_id']))