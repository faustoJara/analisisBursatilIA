import gradio as gr
import joblib
import numpy as np

model = joblib.load('xgb_direccional_nvda.pkl')
scaler = joblib.load('scaler_features.pkl')

def predecir_direccion(close, volume, news_volume):
    try:
        log_volume = np.log1p(float(volume))
        log_news = np.log1p(float(news_volume))
        
        features_continuas = np.array([[float(close), float(volume), float(news_volume), log_volume, log_news]])
        features_escaladas = scaler.transform(features_continuas)
        
        num_features = model.n_features_in_
        vector_final = np.zeros((1, num_features))
        vector_final[0, :5] = features_escaladas[0] 
        
        pred_clase = model.predict(vector_final)[0]
        pred_prob = model.predict_proba(vector_final)[0]
        
        prob_sube = pred_prob[1] * 100
        prob_baja = pred_prob[0] * 100
        
        resultado = "🚀 TENDENCIA ALCISTA (BUY)" if pred_clase == 1 else "📉 TENDENCIA BAJISTA (SELL/HOLD)"
        detalles = f"Probabilidad de Subida: {prob_sube:.2f}% | Probabilidad de Bajada: {prob_baja:.2f}%"
        
        return resultado, detalles
    except Exception as e:
        return "Error en el procesamiento", str(e)

interface = gr.Interface(
    fn=predecir_direccion,
    inputs=[
        gr.Number(label="Precio de Cierre Actual (Close USD)"),
        gr.Number(label="Volumen de Transacciones Financieras"),
        gr.Number(label="Volumen de Noticias Diario (Data Lake)")
    ],
    outputs=[
        gr.Text(label="Señal de HedgeMind"),
        gr.Text(label="Probabilidades Estadísticas")
    ],
    title="HedgeMind AI - Motor Direccional de NVIDIA",
    description="Simulador de inferencia en tiempo real. Introduce métricas para evaluar la probabilidad direccional."
)

if __name__ == "__main__":
    interface.launch()
