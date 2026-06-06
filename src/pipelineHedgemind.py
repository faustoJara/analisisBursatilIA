"""
===============================================================================
PROYECTO: HedgeMind AI - Pipeline de Datos (Hito 4)
AUTOR: Fausto Jara Buncay
DESCRIPCIÓN:Script unificado para la ingesta, integración y procesamiento 
            de datos bimodales (Finanzas + NLP News). Extrae datos crudos 
            desde APIs y MongoDB (Data Lake), Nifi, kafka, aplica transformaciones de 
            ingeniería de características y almacena el dataset final en 
            AWS RDS (Data Warehouse) listo para el consumo de Machine Learning.
===============================================================================
"""

import os
import logging
import pandas as pd
import numpy as np
import yfinance as yf
import pymongo
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
# =============================================================================
# 0. CONFIGURACIÓN DEL ENTORNO Y LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno (.env)
load_dotenv(find_dotenv())

def get_rds_engine():
    """Establece conexión con el Data Warehouse en AWS RDS."""
    try:
        conexion_str = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        engine = create_engine(conexion_str)
        return engine
    except Exception as e:
        logger.error(f"Error conectando a AWS RDS: {e}")
        raise

def get_mongo_client():
    """Establece conexión con el Data Lake en MongoDB Atlas."""
    try:
        cliente = pymongo.MongoClient(os.getenv("MONGO_URI"))
        return cliente["hedgemind_db"]
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise

# =============================================================================
# 1. EXTRACCIÓN DE DATOS (INGESTA)
# =============================================================================
def extraccion_financiera(engine):
    """Descarga datos bursátiles de NVIDIA y guarda el crudo en RDS."""
    logger.info("Iniciando extracción de datos financieros (Yahoo Finance)...")
    df_finance = yf.download("NVDA", period="max", progress=False)
    
    if isinstance(df_finance.columns, pd.MultiIndex):
        df_finance.columns = df_finance.columns.get_level_values(0)
    
    df_finance.to_sql('raw_nvda_finance', con=engine, if_exists='replace', index=True)
    logger.info(f"Datos financieros crudos guardados en RDS. Dimensiones: {df_finance.shape}")
    
    df_finance.index = pd.to_datetime(df_finance.index)
    df_finance.index.name = 'fecha'
    return df_finance

def extraccion_noticias(db):
    """Agrupa el volumen de noticias por día desde múltiples colecciones."""
    logger.info("Iniciando extracción y unificación de metadatos del Data Lake...")
    colecciones = ["finnhubNVDA", "googleNVDA", "kaggleNVDA", "sentimiento_crudo"]
    noticias_list = []

    for col in colecciones:
        cursor = db[col].find({}, {"date": 1, "_id": 0})
        df_col = pd.DataFrame(list(cursor))
        if not df_col.empty:
            noticias_list.append(df_col)

    if noticias_list:
        df_todas = pd.concat(noticias_list, ignore_index=True)
        df_todas['date'] = pd.to_datetime(df_todas['date'], errors='coerce').dt.date
        df_todas = df_todas.dropna(subset=['date'])
        
        volumen_noticias = df_todas.groupby('date').size().reset_index(name='news_volume')
        volumen_noticias['date'] = pd.to_datetime(volumen_noticias['date'])
        volumen_noticias.set_index('date', inplace=True)
        volumen_noticias.index.name = 'fecha'
        
        logger.info(f"Metadatos extraídos. Días con noticias registradas: {len(volumen_noticias)}")
        return volumen_noticias
    else:
        logger.warning("No se encontraron noticias en MongoDB.")
        return pd.DataFrame(columns=['news_volume'])

# =============================================================================
# 2. TRANSFORMACIÓN Y LIMPIEZA (PROCESAMIENTO)
# =============================================================================
def procesar_e_integrar(df_finance, volumen_noticias):
    """Fusiona los datasets, limpia inconsistencias y genera características."""
    logger.info("Integrando fuentes de datos (Left Join)...")
    df_integrado = df_finance.join(volumen_noticias, how='left')
    df_integrado = df_integrado.drop_duplicates()

    logger.info("Iniciando limpieza y Feature Engineering...")
    # 1. Limpieza de columnas redundantes
    cols_eliminar = ['Open', 'High', 'Low', 'Adj Close']
    df_limpio = df_integrado.drop(columns=[col for col in cols_eliminar if col in df_integrado.columns])
    
    # 2. Imputación de nulos
    df_limpio['news_volume'] = df_limpio['news_volume'].fillna(0)
    df_limpio['Close'] = df_limpio['Close'].ffill()
    df_limpio['Volume'] = df_limpio['Volume'].ffill()
    
    # 3. Transformaciones logarítmicas (Outliers)
    df_limpio['log_Volume'] = np.log1p(df_limpio['Volume'])
    df_limpio['log_news_volume'] = np.log1p(df_limpio['news_volume'])
    
    # 4. Target Return y Descomposición temporal
    df_limpio['dia'] = df_limpio.index.day
    df_limpio['mes'] = df_limpio.index.month
    df_limpio['dia_semana'] = df_limpio.index.dayofweek
    df_limpio['Target_Return'] = df_limpio['Close'].pct_change().shift(-1)
    df_limpio = df_limpio.dropna(subset=['Target_Return'])
    
    # 5. Discretización y Encoding
    bins_volumen = [
        df_limpio['Volume'].min() - 1, 
        df_limpio['Volume'].quantile(0.33), 
        df_limpio['Volume'].quantile(0.66), 
        df_limpio['Volume'].max()
    ]
    df_limpio['categoria_volumen'] = pd.cut(df_limpio['Volume'], bins=bins_volumen, labels=['Volumen_Bajo', 'Volumen_Medio', 'Volumen_Alto'])
    df_final = pd.get_dummies(df_limpio, columns=['categoria_volumen', 'mes', 'dia_semana'], drop_first=True)
    
    # Asegurar compatibilidad estricta de tipos booleanos
    for col in df_final.columns:
        if df_final[col].dtype == bool:
            df_final[col] = df_final[col].astype(int)
            
    logger.info(f"Dataset estructurado finalizado. Dimensiones: {df_final.shape}")
    return df_final

# =============================================================================
# 3. CARGA (ALMACENAMIENTO EN DATA WAREHOUSE)
# =============================================================================
def inyectar_a_rds(df_final, engine):
    """Guarda el dataset de entrenamiento definitivo en la nube."""
    nombre_tabla = 'datasetEntrenamiento'
    logger.info(f"Inyectando tabla '{nombre_tabla}' en AWS RDS...")
    
    df_final.to_sql(name=nombre_tabla, con=engine, if_exists='replace', index=True, chunksize=1000)
    logger.info("✅ Pipeline ETL ejecutado con éxito. Datos listos para Machine Learning.")

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE DE HEDGEMIND AI ===")
    try:
        # Conexiones
        rds_engine = get_rds_engine()
        mongo_db = get_mongo_client()
        
        # Flujo de datos
        df_fin = extraccion_financiera(rds_engine)
        df_news = extraccion_noticias(mongo_db)
        
        df_maestro = procesar_e_integrar(df_fin, df_news)
        inyectar_a_rds(df_maestro, rds_engine)
        
    except Exception as e:
        logger.error(f"Fallo crítico en la ejecución del pipeline: {e}")