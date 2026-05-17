# HedgeMind-NVDA 🚀 📈

### Sistema Híbrido de Predicción Bursátil Mediante Ingeniería de Datos y Análisis de Sentimiento

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![PyTorch 2.6.0](https://img.shields.io/badge/PyTorch-2.6.0--cu124-orange.svg)](https://pytorch.org/)
[![CUDA 12.4](https://img.shields.io/badge/CUDA-12.4-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Apache NiFi](https://img.shields.io/badge/Apache-NiFi-svg.svg?color=teal)](https://nifi.apache.org/)

**HedgeMind-NVDA** es un ecosistema híbrido de Inteligencia Artificial e Ingeniería de Datos diseñado para predecir la variación porcentual diaria del activo **NVIDIA Corporation (NASDAQ: NVDA)**. 

A diferencia de los modelos tradicionales basados exclusivamente en series temporales cuantitativas, este sistema implementa una arquitectura que fusiona indicadores técnicos de mercado con el análisis de sentimiento masivo de noticias financieras recopiladas en tiempo real mediante Procesamiento de Lenguaje Natural (NLP).

---

## 🏗️ Arquitectura del Sistema (Data Pipeline)

El proyecto está diseñado bajo un enfoque conceptual "Local-First/Nube Híbrida" de coste cero, optimizado para ejecutarse localmente con soporte de aceleración por hardware:

1. **Ingesta y Streaming:** **Apache NiFi** actúa como el extractor perimetral consumiendo APIs de noticias financieras de forma continua. Los datos se transmiten con baja latencia a través de un clúster local de **Apache Kafka**.
2. **Almacenamiento Híbrido:**
   * **NoSQL (MongoDB Atlas):** Almacena el flujo de noticias crudas en formato JSON/BSON flexible.
   * **Data Lake (Amazon S3 / LocalStack):** Resguardo inmutable de las series temporales históricas descargadas de Yahoo Finance (`yfinance`).
   * **Relacional (Amazon RDS / SQLite):** Repositorio único final donde se consolida el *Dataset Maestro* estructurado e indexado por fecha.
3. **Procesamiento ETL (AWS Glue Logic):** Proceso encargado de realizar la ingeniería de características (cálculo de RSI, Medias Móviles), extracción del sentiment score empleando el modelo *FinBERT* de Hugging Face y unificación de las fuentes.

---

## 🛠️ Requisitos del Sistema y Stack Técnico

* **Sistema Operativo:** Windows 10/11 (Optimizado para arquitecturas x64)
* **Entorno de Desarrollo:** Visual Studio Code (VSC)
* **Hardware Recomendado:** NVIDIA GeForce RTX 4060 (Laptop GPU) con soporte para núcleos Tensor.
* **Stack Core:**
  * Miniconda / Anaconda Navigator
  * CUDA Toolkit 12.4 & cuDNN integrado
  * Python 3.10.x
  * PyTorch 2.6.0 con soporte CUDA operativo

---

## 🚀 Instalación y Configuración del Entorno

Sigue estos pasos en orden cronológico para replicar el entorno de desarrollo local en tu terminal de VS Code:

### 1. Clonar el repositorio e ingresar al directorio
```bash
git clone [https://github.com/tu-usuario/HedgeMind-NVDA.git](https://github.com/tu-usuario/HedgeMind-NVDA.git)
cd HedgeMind-NVDA
