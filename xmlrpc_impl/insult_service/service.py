# xmlrpc_impl/insult_service/service.py
"""
InsultService (XML-RPC)
- add_insult(text)
- get_insults()
- subscribe(host,port)
- broadcaster envía un insulto aleatorio cada 5s a subscriptores
"""
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import multiprocessing, time, random, xmlrpc.client

class InsultService:
    def __init__(self, insults, subscribers):
        self.insults = insults        # multiprocessing.Manager().list()
        self.subscribers = subscribers  # multiprocessing.Manager().list()

    def add_insult(self, text):
        if text not in self.insults:
            self.insults.append(text)
            return True
        return False

    def get_insults(self):
        return list(self.insults)

    def subscribe(self, host, port):
        sub = (host, port)
        if sub not in self.subscribers:
            self.subscribers.append(sub)
        return True

    def _broadcaster(self):
        # lee periódicamente insultos y subs
        while True:
            time.sleep(5)
            if not self.insults or not self.subscribers:
                continue
            insult = random.choice(self.insults)
            for host, port in list(self.subscribers):
                try:
                    proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}', allow_none=True)
                    proxy.receive_insult(insult)
                except:
                    pass


def main():
    # Estado compartido por Manager
    mgr = multiprocessing.Manager()
    insults = mgr.list()
    subscribers = mgr.list()

    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    server = SimpleXMLRPCServer(('0.0.0.0', 8000), requestHandler=RequestHandler, allow_none=True)
    svc = InsultService(insults, subscribers)
    server.register_instance(svc)

    # broadcaster en proceso separado
    broadcaster_proc = multiprocessing.Process(target=svc._broadcaster, daemon=True)
    broadcaster_proc.start()

    print("[InsultService] corriendo en puerto 8000...")
    server.serve_forever()


if __name__ == '__main__':
    main()