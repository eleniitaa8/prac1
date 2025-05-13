import redis
import threading
import json

class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379, max_connections=10):
        # Creamos un ConnectionPool con un límite de conexiones simultáneas
        pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            max_connections=max_connections
        )
        # Todas las operaciones usarán este pool
        self.r = redis.Redis(connection_pool=pool)

        self.insults_key = 'insults'
        self.channel = 'insults_channel'

        # Inicializamos el cache con los insultos ya existentes
        self.insults_cache = set(self.r.smembers(self.insults_key))

        # Lanzamos hilo en background para mantener el cache actualizado
        t = threading.Thread(target=self._listen_insults, daemon=True)
        t.start()

    def _listen_insults(self):
        pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self.channel)
        for msg in pubsub.listen():
            # msg['data'] es la nueva palabra añadida
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
            # sustituimos cada insulto en cache
            for ins in self.insults_cache:
                filtered = filtered.replace(ins, 'CENSORED')

            resp = {'filtered': filtered}
            self.r.rpush(response_stream, json.dumps(resp))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host',     default='localhost')
    parser.add_argument('--redis-port',     type=int, default=6379)
    parser.add_argument(
        '--max-connections',
        type=int,
        default=50,
        help='Máximo de conexiones simultáneas en el pool'
    )
    args = parser.parse_args()

    service = InsultFilterService(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        max_connections=args.max_connections
    )
    service.start()