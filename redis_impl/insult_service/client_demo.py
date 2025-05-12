import redis
import threading
import json
import uuid
import time


def listen_insults():
    r = redis.Redis(decode_responses=True)
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('insults_channel')
    for message in pubsub.listen():
        print("[Subscriber] New insult:", message['data'])


def main():
    r = redis.Redis(decode_responses=True)
    client_id = str(uuid.uuid4())
    response_stream = f"insult_responses:{client_id}"

    # Start background listener for published insults
    t = threading.Thread(target=listen_insults, daemon=True)
    t.start()

    # Add some insults
    for insult in ["dunderhead", "lummox", "scoundrel"]:
        req = {'command': 'add_insult', 'insult': insult, 'client_id': client_id}
        r.rpush('insult_requests', json.dumps(req))
        resp = json.loads(r.blpop(response_stream, timeout=5)[1])
        print(f"Added '{insult}': {resp['added']}")
        time.sleep(1)

    # Retrieve all insults
    req = {'command': 'get_insults', 'client_id': client_id}
    r.rpush('insult_requests', json.dumps(req))
    resp = json.loads(r.blpop(response_stream, timeout=5)[1])
    print("Current insults:", resp['insults'])

    # Give some time for subscriber to receive any additional messages
    time.sleep(5)

if __name__ == '__main__':
    main()