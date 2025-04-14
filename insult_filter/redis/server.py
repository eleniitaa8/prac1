import redis
import time
import re
from flask import Flask, request, jsonify

# Conexión a Redis y variables
r = redis.Redis(host='localhost', port=6379, db=1)
RESULTS_KEY = "filtered_results"
INSULTS = ["nincompoop", "idiot", "fool"]

def filter_text(text):
    filtered = text
    for insult in INSULTS:
        filtered = re.sub(insult, "CENSORED", filtered, flags=re.IGNORECASE)
    # Guardar el resultado en Redis (usamos una lista)
    r.rpush(RESULTS_KEY, filtered)
    return filtered

app = Flask(__name__)

@app.route("/filter", methods=["POST"])
def filter_text_route():
    text = request.json.get("text")
    filtered = filter_text(text)
    return jsonify({"filtered": filtered})

@app.route("/get_results", methods=["GET"])
def get_results_route():
    # Obtener todos los resultados
    results = [s.decode() for s in r.lrange(RESULTS_KEY, 0, -1)]
    return jsonify({"results": results})

if __name__ == "__main__":
    print("Redis-based InsultFilter server running on port 9001...")
    app.run(port=9001)
