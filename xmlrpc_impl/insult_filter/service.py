# xmlrpc_impl/insult_filter/service.py
"""
InsultFilterService (XML-RPC)
- add_text(text): filtra insultos de InsultService y guarda resultado
- get_results(): devuelve lista de textos filtrados
"""
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client, redis, time, re, argparse, sys, threading

class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.results_key = 'results'
        self.pub_channel  = 'insults_pubsub'
        # carga inicial cacheada
        self.insults_cache = set(self.r.smembers(self.insults_key))
        self._compile_pattern()
        self.r.delete(self.results_key)
        # hilo de pub/sub
        t = threading.Thread(target=self._listen_insults, daemon=True)
        t.start()

    def _compile_pattern(self):
        if self.insults_cache:
            pat = r'\b(' + '|'.join(map(re.escape, self.insults_cache)) + r')\b'
            self.re_pat = re.compile(pat)
        else:
            self.re_pat = None

    def _listen_insults(self):
        pub = self.r.pubsub()
        pub.subscribe(self.pub_channel)
        for msg in pub.listen():
            if msg['type']=='message':
                insult = msg['data']
                # actualizar caché y regex
                if insult not in self.insults_cache:
                    self.insults_cache.add(insult)
                    self._compile_pattern()

    def add_text(self, text):
        # filtrar usando la regex cacheada
        if self.re_pat:
            filtered = self.re_pat.sub('CENSORED', text)
        else:
            filtered = text
        # pipeline para agrupar la escritura
        pipe = self.r.pipeline()
        pipe.rpush(self.results_key, filtered)
        pipe.execute()
        return True

    def get_results(self):
        return self.r.lrange(self.results_key, 0, -1)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--port', type=int, default=8010)
    args, _ = parser.parse_known_args()
    port = args.port

    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    server = SimpleXMLRPCServer(('0.0.0.0', port), requestHandler=RequestHandler, allow_none=True)
    svc = InsultFilterService()
    server.register_instance(svc)

    print(f"[InsultFilter] corriendo en puerto {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()