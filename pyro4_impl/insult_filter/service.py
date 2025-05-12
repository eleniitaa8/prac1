import argparse
import Pyro4
import redis
import threading

@Pyro4.expose
class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        # Conexión Redis para insults y resultados
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.results_key = 'filtered_results'
        # cache local: arranca con lo que hay en Redis
        self.insults_cache = set(self.r.smembers(self.insults_key))
        self.r.delete(self.results_key)
        # lanza hilo de suscripción a pub/sub
        t = threading.Thread(target=self._listen_insults, daemon=True)
        t.start()

    def _listen_insults(self):
        pubsub = self.r.pubsub()
        pubsub.subscribe('insults_pubsub')
        for message in pubsub.listen():
            if message['type'] == 'message':
                self.insults_cache.add(message['data'])  # cachea sólo el nuevo insulto

    def add_text(self, text):
        # insults = list(self.r.smembers(self.insults_key))
        out = text
        for ins in self.insults_cache:
            out = out.replace(ins, 'CENSORED')
        # batching: usamos pipeline para agrupar múltiples RPUSH
        pipe = self.r.pipeline()
        pipe.rpush(self.results_key, out)
        pipe.execute()
        return True

    def get_results(self):
        return self.r.lrange(self.results_key, 0, -1)


def main():
    parser = argparse.ArgumentParser(description='Pyro InsultFilterService with Redis backend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the Pyro daemon')
    parser.add_argument('--port', type=int, required=True, help='Port to bind the Pyro daemon')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    args = parser.parse_args()

    service = InsultFilterService(args.redis_host, args.redis_port)

    daemon = Pyro4.Daemon(host=args.host, port=args.port)
    uri = daemon.register(service, objectId="InsultFilterService")
    print(f"[InsultFilterService] URI: {uri}")
    daemon.requestLoop()


if __name__=='__main__':
    main()