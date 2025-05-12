import redis
import uuid
import json
import time


def main():
    r = redis.Redis(decode_responses=True)
    client_id = str(uuid.uuid4())
    response_stream = f"filter_responses:{client_id}"

    texts = [
        "You are such a lummox!",
        "My dunderhead friend laughs.",
        "Scoundrel behavior is unacceptable."
    ]
    for text in texts:
        req = {'text': text, 'client_id': client_id}
        r.rpush('filter_requests', json.dumps(req))
        resp = json.loads(r.blpop(response_stream, timeout=5)[1])
        print(f"Original: {text}")
        print(f"Filtered: {resp['filtered']}\n")
        time.sleep(1)

if __name__ == '__main__':
    main()