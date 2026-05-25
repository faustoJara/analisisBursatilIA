import sys
import os
import torch
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine # Librería real para conectar con bases de datos

# Cargar las credenciales reales de tu archivo .env
load_dotenv()

# ==============================================================================
# CONFIGURACIÓN DEL SISTEMA DE LOGGING
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("HedgeMind_Pipeline")

logger.info("==============================================================================")
logger.info("INICIALIZANDO SCRIPT: CONEXIONES AWS Y PROCESAMIENTO")
logger.info("==============================================================================")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if torch.cuda.is_available():
    logger.info(f"🏎️ ACELERACIÓN POR HARDWARE DETECTADA: {torch.cuda.get_device_name(0)}")
else:
    logger.warning("⚠️ ALERTA: No se detectaron núcleos CUDA operativos. Usando CPU.")
print("-" * 78)

class HedgeMindDataPipeline:
    def __init__(self, ticker: str, start_date: str):
        self.ticker = ticker
        self.start_date = start_date
        self.dataset_raw_market = None
        self.dataset_master_sql = None
        self.engine = None # Motor SQL

    def fase_1_despliegue_arquitectura(self):
        logger.info("[ETAPA 1/4]: Verificando conectividad de la arquitectura Cloud...")
        try:
            db_user = os.getenv("DB_USER")
            db_pass = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT") # Debe ser 3306 en tu .env
            db_name = os.getenv("DB_NAME")
            
            # Conector de MySQL/MariaDB
            conexion_str = f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            self.engine = create_engine(conexion_str)
            
            # Intentamos abrir la puerta de AWS para confirmar que la contraseña y el puerto son correctos
            with self.engine.connect() as conn:
                logger.info("  ✅ Connection Status: Amazon RDS MariaDB Cloud")
                
        except Exception as e:
            logger.error(f"Fallo crítico conectando a Amazon RDS. Revisa tu .env y el Grupo de Seguridad de AWS: {str(e)}")
            raise e

    def fase_2_ingesta_multifuente(self):
        """Descarga datos reales del mercado."""
        logger.info(f"[ETAPA 2/4]: Iniciando ingesta masiva para el activo: {self.ticker}")
        
        try:
            logger.info(f"  📥 Descargando datos REALES de Yahoo Finance API desde {self.start_date}...")
            self.dataset_raw_market = yf.download(self.ticker, start=self.start_date, progress=False)
            logger.info(f"  ✅ Descarga completada. Días de cotización: {len(self.dataset_raw_market)}.")
        except Exception as e:
            logger.error(f"Error en la descarga de datos: {str(e)}")
            raise e

        # NOTA: Simulamos el NLP aquí temporalmente hasta que conectemos el modelo de lenguaje a Mongo en el Hito 2
        logger.info("  📥 Generando simulador temporal de sentiento para estructurar la tabla...")
        np.random.seed(42)  
        self.sentiment_stream = np.random.uniform(-1, 1, size=len(self.dataset_raw_market))
        self.news_volume_stream = np.random.randint(1, 100, size=len(self.dataset_raw_market))

    def fase_3_procesamiento_y_feature_engineering(self):
        """Transformación y matemáticas."""
        logger.info("[ETAPA 3/4]: Ejecutando motor ETL...")
        
        df_master = pd.DataFrame(index=self.dataset_raw_market.index)
        
        # Corrección de estructura MultiIndex de yfinance
        if isinstance(df_master.columns, pd.MultiIndex):
            df_master.columns = df_master.columns.droplevel(1)
            
        df_master['close_price'] = self.dataset_raw_market['Close'].values.flatten()
        df_master['trading_volume'] = self.dataset_raw_market['Volume'].values.flatten()
        
        logger.info("  ⚙️ Calculando Oscilador de Fuerza Relativa (RSI 14)...")
        delta = df_master['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9) 
        df_master['rsi_14'] = 100 - (100 / (1 + rs))
        
        df_master['sentiment_score'] = self.sentiment_stream
        df_master['news_volume'] = self.news_volume_stream
        
        logger.info("  ⚙️ Generando Variable Objetivo (Target_Return)...")
        df_master['target_return'] = df_master['close_price'].pct_change().shift(-1)
        
        df_master.dropna(inplace=True)
        self.dataset_master_sql = df_master

    def fase_4_persistencia_rds(self):
        """GUARDADO FÍSICO Y REAL EN AMAZON AWS."""
        logger.info("[ETAPA 4/4]: Escribiendo datos físicos en Amazon RDS...")
        try:
            # Esta línea es la que manda el comando SQL real a Amazon
            self.dataset_master_sql.to_sql(
                name='dataset_nvda_unificado', # Nombre de la tabla en MariaDB
                con=self.engine, 
                if_exists='replace', # Si la tabla existe, la sobrescribe con datos frescos
                index=True, 
                index_label='fecha'
            )
            logger.info(f"  💾 Datos GUARDADOS EXITOSAMENTE en la nube de AWS. Tamaño: {self.dataset_master_sql.shape}")
        except Exception as e:
            logger.error(f"Error crítico al guardar en la base de datos AWS: {str(e)}")
            raise e

# ==============================================================================
if __name__ == "__main__":
    pipeline = HedgeMindDataPipeline(ticker="NVDA", start_date="1900-01-01")
    
    pipeline.fase_1_despliegue_arquitectura()
    pipeline.fase_2_ingesta_multifuente()
    pipeline.fase_3_procesamiento_y_feature_engineering()
    pipeline.fase_4_persistencia_rds()
    
    print("\n✅ VISTA PREVIA DEL DATASET MAESTRO (El mismo que ahora está en AWS):")
    print(pipeline.dataset_master_sql.tail(5))