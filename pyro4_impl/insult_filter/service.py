import argparse
import Pyro4
import redis

@Pyro4.expose
class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        # Conexión Redis para insults y resultados
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.results_key = 'filtered_results'
        self.r.delete(self.results_key)

    def add_text(self, text):
        insults = list(self.r.smembers(self.insults_key))
        out = text
        for ins in insults:
            out = out.replace(ins, 'CENSORED')
        self.r.rpush(self.results_key, out)
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