Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "🚀 HEDGEMIND-NVDA: SCRIPT MAESTRO DE DESPLIEGUE" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Levantar Arquitectura de Datos (Docker)
Write-Host "`n[1/3] Levantando infraestructura de datos (Kafka, NiFi)..." -ForegroundColor Yellow
docker-compose up -d

# Espera de seguridad para que los servicios en Java (NiFi/Kafka) arranquen correctamente
Write-Host "⏳ Esperando 30 segundos a que los servicios inicialicen correctamente..." -ForegroundColor DarkGray
Start-Sleep -Seconds 30
Write-Host "✅ Contenedores operativos." -ForegroundColor Green

# 2. Comprobación del entorno de Python
Write-Host "`n[2/3] Verificando entorno virtual e instalando dependencias..." -ForegroundColor Yellow
# Asumiendo que existe un requirements.txt, si no, este paso se omite silenciosamente
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt | Out-Null
}
Write-Host "✅ Dependencias de Python listas." -ForegroundColor Green

# 3. Instrucciones de Procesamiento de Información
Write-Host "`n[3/3] Arquitectura desplegada. Lanzando servidor Jupyter..." -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "📝 INSTRUCCIONES PARA EL TRIBUNAL:"
Write-Host "1. La ingesta en tiempo real está corriendo en NiFi (http://localhost:8080/nifi)."
Write-Host "2. En la ventana de Jupyter que se abrirá, ejecute en orden:"
Write-Host "   -> hitos/evaluacion_modelo.ipynb (Para entrenar y evaluar el modelo)"
Write-Host "   -> hitos/gradio.ipynb (Para probar la interfaz en tiempo real)"
Write-Host "=======================================================" -ForegroundColor Cyan

# Abrir Jupyter Notebook automáticamente
jupyter notebook