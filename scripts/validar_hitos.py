import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar al Dataset Maestro
db = mysql.connector.connect(host=os.getenv("DB_HOST"), 
                            user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD"),
                            database="tfm_db")

# 1. Hito 1: Validación EDA (Visualización de distribución de sentimiento)
def validar_hito_1():
    df = pd.read_sql("SELECT sentimiento, volumen_noticias FROM nvidia_historico", db)
    print("📊 Hito 1: Realizando EDA rápido...")
    df.hist(bins=20, figsize=(10, 5))
    plt.show() # Esto valida que los datos fluyen y son visualizables

# 2. Hito 2: Validación Modelo (Estructura para entrenamiento)
def validar_hito_2():
    df = pd.read_sql("SELECT * FROM nvidia_historico", db)
    # Verificamos que tenemos los datos para el Target (mañana lo usaremos para XGBoost)
    print(f"🧠 Hito 2: Dataset preparado con {len(df)} registros.")
    print(df.head())

validar_hito_1()
validar_hito_2()