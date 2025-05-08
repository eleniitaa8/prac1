import Pyro4
import argparse, threading, time, random, Pyro4, redis

@Pyro4.expose
class InsultService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        # Conexión a Redis para estado compartido
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.subs_key = 'subscribers'
        # Limpiar estado previo
        self.r.delete(self.insults_key, self.subs_key)

    def add_insult(self, text):
        # Añade insulto si no existe
        added = self.r.sadd(self.insults_key, text)
        if added:
            # Notificar inmediatamente a suscriptores activos
            subs = list(self.r.smembers(self.subs_key))
            for sub in subs:
                try:
                    host, port = sub.split(':')
                    uri = f"PYRO:CallbackServer@{host}:{port}"
                    proxy = Pyro4.Proxy(uri)
                    proxy.receive_insult(text)
                except Exception:
                    # Eliminar suscriptor caído
                    self.r.srem(self.subs_key, sub)
        return bool(added)

    def get_insults(self):
        # Recupera todos los insultos
        return list(self.r.smembers(self.insults_key))

    def subscribe(self, host, port):
        # Registrar suscriptor (host:port)
        sub = f"{host}:{port}"
        self.r.sadd(self.subs_key, sub)
        return True

    def _broadcaster(self):
        # Envíos periódicos cada 5s
        while True:
            time.sleep(5)
            insults = list(self.r.smembers(self.insults_key))
            subs = list(self.r.smembers(self.subs_key))
            if not insults or not subs:
                continue
            insult = random.choice(insults)
            for sub in subs:
                try:
                    host, port = sub.split(':')
                    uri = f"PYRO:CallbackServer@{host}:{port}"
                    proxy = Pyro4.Proxy(uri)
                    proxy.receive_insult(insult)
                except Exception:
                    self.r.srem(self.subs_key, sub)

def main():
    parser = argparse.ArgumentParser(description='Pyro InsultService with Redis backend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the Pyro daemon')
    parser.add_argument('--port', type=int, required=True, help='Port to bind the Pyro daemon')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    args = parser.parse_args()

    service = InsultService(args.redis_host, args.redis_port)

    # Lanzar broadcaster en hilo demonio
    threading.Thread(target=service._broadcaster, daemon=True).start()

    # Configurar Pyro Daemon
    daemon = Pyro4.Daemon(host=args.host, port=args.port)
    uri = daemon.register(service, objectId="InsultService")
    print(f"[InsultService] URI: {uri}")
    daemon.requestLoop()

if __name__ == '__main__':
    main()