import redis
import threading
import json

class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.channel = 'insults_channel'
        # Initial cache from Redis
        self.insults_cache = set(self.r.smembers(self.insults_key))
        # Start pub/sub to keep cache updated
        t = threading.Thread(target=self._listen_insults, daemon=True)
        t.start()

    def _listen_insults(self):
        pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self.channel)
        for msg in pubsub.listen():
            self.insults_cache.add(msg['data'])

    def start(self):
        print("[InsultFilterService] Listening for requests on 'filter_requests'...")
        while True:
            _, message = self.r.blpop('filter_requests')
            req = json.loads(message)
            text = req.get('text', '')
            client_id = req.get('client_id')
            response_stream = f"filter_responses:{client_id}"
            filtered = text
            for ins in self.insults_cache:
                filtered = filtered.replace(ins, 'CENSORED')
            resp = {'filtered': filtered}
            self.r.rpush(response_stream, json.dumps(resp))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host', default='localhost')
    parser.add_argument('--redis-port', type=int, default=6379)
    args = parser.parse_args()
    service = InsultFilterService(args.redis_host, args.redis_port)
    service.start()