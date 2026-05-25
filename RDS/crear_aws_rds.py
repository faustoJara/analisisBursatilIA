import os
import time
import boto3
import mysql.connector
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()
# --- CONFIGURACIÓN AWS ---
DB_INSTANCE_ID = os.getenv("DB_INSTANCE_ID")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Parámetros de capa gratuita (Free Tier)
DB_INSTANCE_CLASS = "db.t3.micro" 
DB_ENGINE = "mariadb"
DB_ALLOCATED_STORAGE = 20

# Iniciar sesión en AWS
session = boto3.session.Session( 
    aws_access_key_id=os.getenv("ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SECRET_KEY"),
    aws_session_token=os.getenv("SESSION_TOKEN"), # Borrar si no usas cuenta de estudiante temporal
    region_name=os.getenv("REGION")
)
rds = session.client('rds')

def desplegar_y_configurar_rds():
    endpoint = None
    try:
        print(f"🔍 Comprobando si la instancia '{DB_INSTANCE_ID}' ya existe...")
        info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
        endpoint = info['DBInstances'][0]['Endpoint']['Address']
        print(f"✅ La instancia ya existe. Endpoint: {endpoint}")
        
    except ClientError as e:
        print("🚀 Creando nueva instancia RDS (Esto puede tardar entre 5 y 10 minutos)...")
        rds.create_db_instance(
            DBInstanceIdentifier=DB_INSTANCE_ID,
            AllocatedStorage=DB_ALLOCATED_STORAGE,
            DBInstanceClass=DB_INSTANCE_CLASS,
            Engine=DB_ENGINE,
            MasterUsername=DB_USER,
            MasterUserPassword=DB_PASSWORD,
            DBName=DB_NAME,
            PubliclyAccessible=True # Vital para poder conectarnos desde VS Code
        )

        print("⏳ Esperando a que AWS termine de configurar la instancia...")
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=DB_INSTANCE_ID)
        
        info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
        endpoint = info['DBInstances'][0]['Endpoint']['Address']
        print(f"✅ Instancia RDS creada y disponible. Endpoint: {endpoint}")
        
        # Pausa de seguridad para asegurar que el puerto 3306 acepte conexiones
        time.sleep(30) 

    # --- CREACIÓN DE LA TABLA MAESTRA FINANCIERA ---
    print("⚙️ Conectando por MySQL para generar el esquema de datos...")
    try:
        cnx = mysql.connector.connect(
            host=endpoint,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = cnx.cursor()
        
        # Tabla para el modelo de ML (Precios + Sentimiento)
        tabla_nvda = """
        CREATE TABLE IF NOT EXISTS dataset_nvda_unificado (
            fecha DATE PRIMARY KEY,
            close_price FLOAT NOT NULL,
            volumen BIGINT NOT NULL,
            sentiment_score FLOAT NOT NULL,
            news_volume INT NOT NULL,
            target_return FLOAT
        )
        """
        cursor.execute(tabla_nvda)
        cnx.commit()
        print("📊 Tabla 'dataset_nvda_unificado' creada correctamente para el entrenamiento del modelo.")
        
        cursor.close()
        cnx.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Error conectando a la base de datos: {err}")
        print("⚠️ IMPORTANTE: Asegúrate de que el Grupo de Seguridad en AWS permite tráfico entrante en el puerto 3306 desde tu IP (0.0.0.0/0).")

if __name__ == "__main__":
    desplegar_y_configurar_rds()