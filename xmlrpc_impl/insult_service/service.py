from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading, time, random, xmlrpc.client, redis, argparse, sys

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
        # Si se añadió, notificar inmediatamente a subscriptores
        if added:
            subs = self.r.smembers(self.subs_key)
            for sub in subs:
                host, port = sub.split(':')
                try:
                    proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}', allow_none=True)
                    proxy.receive_insult(text)
                except Exception:
                    # Elimina subcriptor caído
                    self.r.srem(self.subs_key, sub)
        return bool(added)

    def get_insults(self):
        return list(self.r.smembers(self.insults_key))

    def subscribe(self, host, port):
        sub = f"{host}:{port}"
        self.r.sadd(self.subs_key, sub)
        return True

    def _broadcaster(self):
        # Envíos periódicos cada 5s
        while True:
            time.sleep(5)
            insults = self.get_insults()
            subs = self.r.smembers(self.subs_key)
            if not insults or not subs:
                continue
            insult = random.choice(insults)
            for sub in list(subs):
                host, port = sub.split(':')
                try:
                    proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}', allow_none=True)
                    proxy.receive_insult(insult)
                except Exception:
                    self.r.srem(self.subs_key, sub)


def main():
    # Ignorar opciones de pytest
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--port', type=int, default=8000)
    args, _ = parser.parse_known_args()
    port = args.port

    # Configurar servidor
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    server = SimpleXMLRPCServer(('localhost', port), requestHandler=RequestHandler, allow_none=True)
    svc = InsultService()
    server.register_instance(svc)

    # Lanzar broadcaster en hilo demonio
    t = threading.Thread(target=svc._broadcaster, daemon=True)
    t.start()

    print(f"[InsultService] corriendo en puerto {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()