import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
load_dotenv()

def inicializar_tabla():
    try:
        # Conexión a tu base de datos
        conn = mysql.connector.connect(
            host= os.getenv("DB_HOST"), # Cambia por tu host real, ej: hedgemind.cxyz.eu-west-1.rds.amazonaws.com
            user= os.getenv("DB_USER"), # Cambia por tu usuario real
            password= os.getenv("DB_PASSWORD"), # Cambia por tu password real
            database="tfm_db"
        )
        cursor = conn.cursor()

        # SQL para crear la tabla
        query = """
        CREATE TABLE IF NOT EXISTS nvidia_historico (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fecha DATE NOT NULL,
            sentimiento FLOAT NOT NULL,
            volumen_noticias INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(query)
        print("✅ Tabla 'nvidia_historico' verificada/creada correctamente.")

    except Error as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    inicializar_tabla()