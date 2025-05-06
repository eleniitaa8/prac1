# xmlrpc_impl/insult_filter/service.py
"""
InsultFilterService (XML-RPC)
- add_text(text): filtra insultos de InsultService y guarda resultado
- get_results(): devuelve lista de textos filtrados
"""
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import multiprocessing, xmlrpc.client

class InsultFilterService:
    def __init__(self, insult_url, results):
        self.insult_url = insult_url
        self.results = results  # multiprocessing.Manager().list()
        self.insults_cache = None

    def _load_insults(self):
        proxy = xmlrpc.client.ServerProxy(self.insult_url, allow_none=True)
        self.insults_cache = proxy.get_insults()

    def add_text(self, text):
        if self.insults_cache is None:
            self._load_insults()
        out = text
        for ins in self.insults_cache:
            out = out.replace(ins, 'CENSORED')
        self.results.append(out)
        return True

    def get_results(self):
        return list(self.results)


def main():
    mgr = multiprocessing.Manager()
    results = mgr.list()
    insult_url = 'http://localhost:8000'

    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    server = SimpleXMLRPCServer(('0.0.0.0', 8010), requestHandler=RequestHandler, allow_none=True)
    svc = InsultFilterService(insult_url, results)
    server.register_instance(svc)

    print("[InsultFilter] corriendo en puerto 8010...")
    server.serve_forever()

if __name__ == '__main__':
    main()