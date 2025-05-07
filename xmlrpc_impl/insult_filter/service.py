# xmlrpc_impl/insult_filter/service.py
"""
InsultFilterService (XML-RPC)
- add_text(text): filtra insultos de InsultService y guarda resultado
- get_results(): devuelve lista de textos filtrados
"""
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client, redis, time, re, argparse, sys

class InsultFilterService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.insults_key = 'insults'
        self.results_key = 'results'
        self.r.delete(self.results_key)
        self.cache = None
        self.cache_ttl = 5
        self.last_load = 0

    def _load_insults(self):
        self.cache = set(self.r.smembers(self.insults_key))
        self.last_load = time.time()
        if self.cache:
            pat = r'\b(' + '|'.join(map(re.escape, self.cache)) + r')\b'
            self.re_pat = re.compile(pat)
        else:
            self.re_pat = None

    def add_text(self, text):
        if self.cache is None or (time.time() - self.last_load) > self.cache_ttl:
            self._load_insults()
        if self.re_pat:
            filtered = self.re_pat.sub('CENSORED', text)
        else:
            filtered = text
        self.r.rpush(self.results_key, filtered)
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