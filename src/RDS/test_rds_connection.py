import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        # Sustituye estos datos por los de tu hedgemind-rds en AWS
        connection = mysql.connector.connect(
            host= os.getenv("DB_HOST"), # Ej: hedgemind.cxyz.eu-west-1.rds.amazonaws.com
            database='tfm_db', 
            user= os.getenv("DB_USER"), # El usuario que configuraste en tu RDS
            password= os.getenv("DB_PASSWORD") # La contraseña que configuraste en tu RDS
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ ¡Conexión exitosa! Conectado a la versión de servidor: {db_info}")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"✅ Base de datos seleccionada: {record}")

    except Error as e:
        print(f"❌ Error al conectar a AWS RDS: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔒 Conexión cerrada.")

if __name__ == "__main__":
    test_connection()