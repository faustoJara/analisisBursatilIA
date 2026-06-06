import redis

# Conectar a Redis (localhost, puerto 6379 por defecto)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("🚀 ÚLTIMO SENTIMIENTO PROCESADO (SPEED LAYER) GUARDADO EN REDIS:")
print("-" * 60)

# Obtener las claves (depende de cómo las hayas guardado en NiFi)
claves = r.keys('*')[:5] # Muestra solo las 5 primeras
for clave in claves:
    valor = r.get(clave)
    print(f"Key: {clave} -> Value: {valor}")
    print("-" * 40)
    
    
    import redis
import json

# Conectar a Redis local
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 1. Simulamos la inserción del JSON crudo de la noticia (lo que haría tu flujo)
noticia_ejemplo = {
    "title": "Will NVIDIA's (NVDA) RTX Spark and Vera AI PC Platform Shift Its End‑to‑End Narrative?",
    "pubDate": "Thu, 04 Jun 2026 08:14:17 +0000",
    "description": "NVIDIA recently used Computex to unveil RTX Spark, its first AI PC superchip co‑developed with Microsoft...",
    "sentiment_score": 0.12738
}

# Guardamos el JSON completo dentro de Redis bajo una clave de la noticia
r.set("nvda_latest_news_json", json.dumps(noticia_ejemplo))

print("📝 VISUALIZACIÓN DE DATOS EN REDIS (SPEED LAYER):")
print("-" * 60)

# 2. Recuperamos las claves y mostramos los datos estructurados
claves = r.keys('*')
for clave in claves:
    valor_puro = r.get(clave)
    
    print(f"🔑 CLAVE REDIS: {clave}")
    
    # Intentamos decodificarlo como JSON para que lo veas bonito
    try:
        datos_json = json.loads(valor_puro)
        print("📄 CONTENIDO (JSON ESTRUCTURADO):")
        print(json.dumps(datos_json, indent=4, ensure_ascii=False))
    except (json.JSONDecodeError, TypeError):
        # Si era el número suelto que tenías antes, lo muestra de forma normal
        print(f"📊 VALOR: {valor_puro}")
        
    print("-" * 40)