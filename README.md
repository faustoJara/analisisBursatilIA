# 📈 HedgeMind AI: Motor Predictivo Direccional para NVIDIA (NVDA)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Integrado-2496ED.svg)
![AWS RDS](https://img.shields.io/badge/AWS_RDS-Data_Warehouse-FF9900.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Data_Lake-47A248.svg)
![XGBoost](https://img.shields.io/badge/Machine_Learning-XGBoost-F37626.svg)
![Hugging Face](https://img.shields.io/badge/Despliegue-Hugging_Face-FFD21E.svg)

**Autor:** Fausto Jara Buncay
**Contexto:** Trabajo de Fin de Máster (TFM) - Arquitectura Big Data e Inteligencia Artificial.

HedgeMind AI es un sistema integral de *Machine Learning* y *Data Engineering* diseñado para predecir la dirección diaria del mercado de la acción de NVIDIA (NVDA). El proyecto combina análisis de series temporales financieras con el Procesamiento de Lenguaje Natural (NLP) aplicado a noticias en tiempo real aplicandolas desde Nifi-kafka-mongodb-Redis.

---

## 🏗️ Arquitectura de Datos y Decisiones Técnicas

El pipeline está diseñado bajo un enfoque robusto de **MLOps**, dividiendo el ciclo de vida del dato en fases claras:

1. **Ingesta y Streaming (NiFi & Kafka):** Se orquesta la captura de noticias en tiempo real mediante Apache NiFi, inyectándolas en tópicos de Kafka para garantizar la resiliencia ante picos de información bursátil.
2. **Data Lake (MongoDB Atlas):** Almacenamiento NoSQL para datos no estructurados (textos crudos de noticias de Finnhub, Google y Kaggle). Elegido por su flexibilidad ante esquemas de texto variables.
3. **Data Warehouse (AWS RDS - MySQL):** Tras el proceso ETL, los datos financieros limpios (Yahoo Finance) y las características extraídas de las noticias se integran estructuralmente en la nube. Se escoge un motor relacional para garantizar la integridad referencial y acelerar las consultas analíticas del modelo.
4. **Machine Learning (XGBoost):** Se optó por transformar el problema de Regresión a **Clasificación Direccional**, optimizado con aceleración por hardware. Frente a modelos como Random Forest o SVR, XGBoost demostró mayor resistencia al sobreajuste (Overfitting) intrínseco del mercado financiero.



## 📂 Estructura del Repositorio


📁 HedgeMind-NVDA-TFM
├── 📁 hitos/                # Cuadernos Jupyter con EDA, entrenamiento y predicción
│   ├── 01_etl_y_eda.ipynb
│   ├── 02_entrenamiento_modelos.ipynb
│   └── 03_despliegue_y_mejoras.ipynb
├── 📁 src/                     # Código fuente y módulos funcionales
│   ├── 📁 huggingFace/         # Artefactos del modelo (.pkl) y app.py de Gradio
│   ├── 📁 mongodb/             # Conectores y scripts de Data Lake
│   ├── 📁 RDS/                 # Conectores y scripts de Data Warehouse
│   └── pipelineHedgemind.py    # Script ETL principal
├── docker-compose.yml          # Infraestructura (NiFi, Kafka, Zookeeper)
├── orquestador_maestro.py      # Script único de despliegue automático
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación técnica

## Para cumplir con la automatización del proyecto, se ha desarrollado un Script Único que levanta la infraestructura y orquesta el procesamiento.


### Pre-requisitos del Sistema:
* **Entorno CUDA (Aceleración por GPU):** Para el procesamiento acelerado de los algoritmos de Machine Learning (XGBoost) y NLP (PyTorch), se requiere una tarjeta gráfica NVIDIA compatible (ej. arquitectura RTX) con los controladores actualizados y el entorno **CUDA Toolkit** configurado en el sistema.
* **Docker Desktop** instalado y en ejecución (para la infraestructura de streaming).
* **Python 3.9 o superior** instalado en el entorno local.
* Archivo `.env` configurado en la raíz con las credenciales de los servicios Cloud (`DB_USER`, `DB_PASSWORD`, `MONGO_URI`,...).

## Ejecución paso a paso:
*Clona este repositorio e instala las dependencias:*

## Crear y acticar el entorno virtual de Conda
*conda create --name tfm_ai python=3.10 -y*
*conda activate tfm_ai*

Bash
pip install -r requirements.txt

## Ejecuta el orquestador maestro:

Bash
python deploy.py