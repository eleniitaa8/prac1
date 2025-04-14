import redis
import time
import random
import threading

# Connect to Redis (assume default parameters)
r = redis.Redis(host='localhost', port=6379, db=0)
INSULTS_KEY = "insults"

def add_insult(insult):
    # Use Redis set to avoid duplicates
    return r.sadd(INSULTS_KEY, insult)

def get_insults():
    return r.smembers(INSULTS_KEY)

def broadcast_insults():
    while True:
        insults = get_insults()
        if insults:
            # Randomly choose an insult (bytes must be decoded)
            insult = random.choice(list(insults)).decode()
            # Publish on a dedicated channel
            r.publish("insult_broadcast", insult)
            print("Broadcasted:", insult)
        time.sleep(5)

if __name__ == "__main__":
    # Start the broadcaster thread.
    threading.Thread(target=broadcast_insults, daemon=True).start()
    
    # For remote access, you can use a lightweight HTTP server such as Flask
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/add_insult", methods=["POST"])
    def add_insult_route():
        insult = request.json.get("insult")
        result = add_insult(insult)
        return jsonify({"added": bool(result)})

    @app.route("/get_insults", methods=["GET"])
    def get_insults_route():
        insults = [s.decode() for s in get_insults()]
        return jsonify({"insults": insults})

    print("Redis-based InsultService running on port 8001...")
    app.run(port=8001)
