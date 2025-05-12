from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading, time, random, xmlrpc.client, redis, argparse, sys, queue

class InsultService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        # Conexión a Redis para estado compartido
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.subs_key = 'subscribers'
        self.pub_channel = 'insults_pubsub'
        # Limpiar estado previo
        self.r.delete(self.insults_key, self.subs_key)
        # Cache local de insultos
        self.local_insults = set()
        # Cola interna para notificaciones callback
        self.cb_queue = queue.Queue()
        # Lanzar worker de callbacks (desacoplado de la ruta crítica)
        threading.Thread(target=self._cb_worker, daemon=True).start()
        # Lanzar broadcaster periódico en hilo demonio
        threading.Thread(target=self._broadcaster, daemon=True).start()

    def add_insult(self, text):
        """
        Añade un insulto si no existe, publica por pub/sub y encola notificación
        para callbacks.
        """
        # Pipeline: SADD + PUBLISH en una sola ida/vuelta a Redis
        pipe = self.r.pipeline()
        pipe.sadd(self.insults_key, text)
        pipe.publish(self.pub_channel, text)
        added, _ = pipe.execute()

        if added:
            # Solo si realmente se añadió al set
            self.cb_queue.put(text)
        return bool(added)

    def get_insults(self):
        """Devuelve la lista completa de insultos."""
        return list(self.r.smembers(self.insults_key))

    def subscribe(self, host, port):
        """
        Registra un subscriber (host:port) para callbacks.
        """
        sub = f"{host}:{port}"
        self.r.sadd(self.subs_key, sub)
        return True

    def _cb_worker(self):
        """
        Worker que procesa la cola de nuevos insultos y llama a
        receive_insult en cada subscriber vía XML-RPC.
        """
        while True:
            insult = self.cb_queue.get()
            subs = list(self.r.smembers(self.subs_key))
            for sub in subs:
                host, port = sub.split(':')
                uri = f'http://{host}:{port}'
                try:
                    proxy = xmlrpc.client.ServerProxy(uri, allow_none=True)
                    proxy.receive_insult(insult)
                except Exception:
                    # Si falla, eliminamos el subscriber
                    self.r.srem(self.subs_key, sub)
            self.cb_queue.task_done()
   
    def _broadcaster(self):
        """
        Cada 5s envía un insulto aleatorio a todos los subscribers,
        encolándolo para que lo repartan los callbacks.
        """
        while True:
            time.sleep(5)
            insults = list(self.r.smembers(self.insults_key))
            if not insults:
                continue
            insult = random.choice(insults)
            # Encolamos para notificar igual que en add_insult
            self.cb_queue.put(insult)


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

    print(f"[InsultService] corriendo en puerto {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()