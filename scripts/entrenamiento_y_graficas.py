import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import mysql.connector
import os
from dotenv import load_dotenv

# ==============================================================================
# 1. EXTRACCIÓN Y CRUCE DE DATOS (AWS RDS -> LOCAL)
# ==============================================================================
print("📥 Conectando a AWS RDS para extraer y cruzar datos históricos...")
load_dotenv()
# Archivo local de entrenamiento mezclando Dataset Técnico y Sentimiento (noticias)
archivo_local = "../datasets/dataset_entrenamiento_final.csv"

try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    
    # LEFT JOIN: Mantenemos toda la historia de precios, rellenando con 0 (Neutral) donde no haya noticias aún
    query = """
        SELECT 
            u.fecha,
            u.close_price,
            u.trading_volume,
            u.rsi_14,
            COALESCE(h.sentimiento, 0) AS sentiment_score,
            COALESCE(h.volumen_noticias, 0) AS news_volume
        FROM dataset_nvda_unificado u
        LEFT JOIN (
            SELECT fecha, AVG(sentimiento) as sentimiento, SUM(volumen_noticias) as volumen_noticias
            FROM nvidia_historico
            GROUP BY fecha
        ) h ON u.fecha = h.fecha
        ORDER BY u.fecha ASC
    """
    
    df = pd.read_sql(query, db)
    db.close()
    print("✅ Datos extraídos y cruzados con éxito. ¡Ya puedes APAGAR AWS RDS!")
    df.to_csv(archivo_local, index=False)

except Exception as e:
    print(f"⚠️ No se pudo conectar a AWS: {e}")
    print(f"📂 Cargando datos desde '{archivo_local}'...")
    df = pd.read_csv(archivo_local)

# ==============================================================================
# 2. INGENIERÍA DE CARACTERÍSTICAS
# ==============================================================================
df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values('fecha')

# Forzar formato numérico
columnas_numericas = ['close_price', 'trading_volume', 'rsi_14', 'sentiment_score', 'news_volume']
for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Target (Retorno logarítmico aproximado con pct_change desplazado al futuro)
df['target_return'] = df['close_price'].pct_change().shift(-1)
df.dropna(inplace=True)

print(f"📈 Filas totales válidas para entrenar la IA: {len(df)}")

features = ['close_price', 'trading_volume', 'rsi_14', 'sentiment_score', 'news_volume']
X = df[features]
y = df['target_return']

# División 80/20 (Respetando el orden del tiempo)
split_idx = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
fechas_test = df['fecha'].iloc[split_idx:]

# ==============================================================================
# 3. ENTRENAMIENTO DEL MODELO XGBOOST
# ==============================================================================
print("🧠 Entrenando modelo XGBoost Regressor (Híbrido)...")
modelo = xgb.XGBRegressor(
    objective='reg:squarederror', 
    n_estimators=150, 
    learning_rate=0.05,
    max_depth=4,
    random_state=42
)
modelo.fit(X_train, y_train)

y_pred = modelo.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
print(f"📊 RESULTADOS -> RMSE: {rmse:.4f} | MAE: {mae:.4f}")

# Guardamos el modelo para usarlo luego en la App de Gradio (Punto 8)
modelo.save_model("xgboost_hedgemind_model.json")
print("💾 Modelo guardado localmente como 'xgboost_hedgemind_model.json'.")

# ==============================================================================
# 4. GENERACIÓN DE GRÁFICAS ACADÉMICAS
# ==============================================================================
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 3, figsize=(22, 6))
fig.suptitle('HedgeMind-NVDA: Evaluación de Predicción de Rendimiento (XGBoost)', fontsize=16, fontweight='bold')

# Gráfica A: Dispersión
axes[0].scatter(y_test, y_pred, alpha=0.6, color='royalblue', edgecolors='w', s=60)
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Predicción Perfecta')
axes[0].set_title('A. Dispersión: Real vs Predicción')
axes[0].set_xlabel('Rendimiento Real')
axes[0].set_ylabel('Rendimiento Predicho')
axes[0].legend()

# Gráfica B: Histograma de Residuos
residuos = y_test - y_pred
sns.histplot(residuos, kde=True, ax=axes[1], color='darkorange', bins=30)
axes[1].axvline(x=0, color='red', linestyle='--', lw=2)
axes[1].set_title('B. Distribución de Residuos (Errores)')
axes[1].set_xlabel('Magnitud del Error')
axes[1].set_ylabel('Frecuencia')

# Gráfica C: Serie Temporal
dias = min(60, len(y_test)) 
axes[2].plot(fechas_test[-dias:], y_test.values[-dias:], label='Real', marker='o', color='black', alpha=0.7)
axes[2].plot(fechas_test[-dias:], y_pred[-dias:], label='Predicción IA', marker='x', color='crimson', lw=2)
axes[2].set_title('C. Serie Temporal (Últimos 60 días)')
axes[2].set_xlabel('Fecha')
axes[2].set_ylabel('Variación Porcentual')
axes[2].tick_params(axis='x', rotation=45)
axes[2].legend()

plt.tight_layout()
plt.savefig("graficas_hito3_hedgemind.png", dpi=300, bbox_inches='tight')
print("📸 Gráficas guardadas (graficas_hito3_hedgemind.png). Abriendo visor...")
plt.show()