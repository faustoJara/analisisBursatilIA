"""
===============================================================================
ORQUESTADOR DE DESPLIEGUE - HEDGEMIND AI (Hito 4)
AUTOR: Fausto Jara Buncay
DESCRIPCIÓN:Script único que despliega la arquitectura de datos (Docker) 
            y orquesta el procesamiento de la información llamando al 
            pipeline ETL principal.
===============================================================================
"""

import os
import subprocess
import time
import logging

# Configuración visual del log para la consola
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def levantar_infraestructura_docker():
    """Ejecuta docker-compose para levantar la infraestructura de streaming y BBDD."""
    logger.info("🐳 Fase 1: Iniciando despliegue de la arquitectura de datos (Docker Compose)...")
    
    # Verificamos que el archivo docker-compose.yml existe en la raíz
    if not os.path.exists("docker-compose.yml"):
        logger.error("❌ No se encontró 'docker-compose.yml' en la raíz del proyecto.")
        raise FileNotFoundError("docker-compose.yml no encontrado.")

    try:
        # Ejecuta docker-compose en modo detached (-d)
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        logger.info("✅ Contenedores levantados correctamente en segundo plano.")
    except Exception as e:
        logger.error(f"❌ Fallo al ejecutar docker-compose: {e}")
        logger.info("Asegúrate de tener Docker Desktop abierto y en ejecución.")
        raise

def esperar_servicios(segundos=20):
    """Pausa la ejecución para permitir que los puertos de Kafka/NiFi se abran."""
    logger.info(f"⏳ Fase 2: Esperando {segundos} segundos a que los servicios estén 'Healthy'...")
    for i in range(segundos, 0, -5):
        logger.info(f"... {i} segundos restantes")
        time.sleep(5)
    logger.info("✅ Servicios de red listos.")

def activar_flujos_nifi():
    """Aviso interactivo para el control manual/visual del evaluador."""
    print("\n" + "="*70)
    logger.info("🌊 Fase 3: Activación de Flujos de Streaming")
    print("⚠️ ACCIÓN REQUERIDA PARA EL TRIBUNAL:")
    print("   1. Abre tu navegador en: http://localhost:8080/nifi")
    print("   2. Inicia el Process Group (botón 'Start') para que Kafka comience a ingerir.")
    print("="*70 + "\n")
    
    input("👉 Presiona [ENTER] cuando el flujo de NiFi esté activado para continuar...")

def ejecutar_pipeline_datos():
    """Lanza el script de procesamiento de datos adaptado a la estructura del proyecto."""
    logger.info("🚀 Fase 4: Iniciando procesamiento de información (ETL)...")
    
    # Ruta del archivo pipelineHedgemind.py dentro de /src/
    ruta_pipeline = os.path.join("src", "pipelineHedgemind.py")
    
    if not os.path.exists(ruta_pipeline):
        logger.error(f"No se encontró el pipeline en la ruta: {ruta_pipeline}")
        raise FileNotFoundError("Script de pipeline no encontrado.")

    try:
        # Llama a tu archivo de procesamiento dentro de /src/
        subprocess.run(["python", ruta_pipeline], check=True)
        logger.info("Pipeline completado: Base de datos RDS actualizada con éxito.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Fallo en el procesamiento de datos del pipeline: {e}")
        raise

if __name__ == "__main__":
    print("\n" + "█"*70)
    print("INICIANDO ORQUESTADOR GLOBAL - HEDGEMIND AI")
    print("█"*70 + "\n")
    
    try:
        levantar_infraestructura_docker()
        esperar_servicios(segundos=20)
        activar_flujos_nifi()
        ejecutar_pipeline_datos()
        
        print("\n" + "█"*70)
        print("DESPLIEGUE Y PROCESAMIENTO FINALIZADOS CON ÉXITO")
        print("El Data Warehouse está actualizado y listo para los modelos de ML.")
        print("█"*70 + "\n")
    except Exception as e:
        print("\nEl despliegue se ha detenido debido a un error previo.")