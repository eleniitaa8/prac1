# xmlrpc_impl/insult_service/client_demo.py
"""
Demo cliente para InsultService:
- arranca un RPC-callback server en puerto 9000
- se subscribe
- añade insultos y muestra lista
- recibe broadcast cada 5s
"""
import time
import xmlrpc.client
import multiprocessing
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# Función a nivel de módulo para evitar cierres que no se puedan pickle
class CallbackHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Función que arranca el servidor de callback en un proceso separado
def run_callback_server(host: str, port: int):
    server = SimpleXMLRPCServer((host, port),
                                 requestHandler=CallbackHandler,
                                 allow_none=True,
                                 logRequests=False)
    def receive_insult(insult):
        print(f"[Broadcast] {insult}")
        return True
    server.register_function(receive_insult)
    print(f"[Callback] escuchando en puerto {port}")
    server.serve_forever()

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = 9000
    # Lanzar servidor de callback en nuevo proceso
    p = multiprocessing.Process(target=run_callback_server, args=(HOST, PORT))
    p.start()
    time.sleep(1)

    # Conectarse al InsultService
    proxy = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
    proxy.subscribe(HOST, PORT)

    # Añadir insultos
    for insult in ('idiot', 'dummy', 'fool'):
        success = proxy.add_insult(insult)
        print(f"Add '{insult}': {success}")

    # Mostrar lista
    print("Lista insultos:", proxy.get_insults())

    # Mantener vivo para recibir broadcasts
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Demo cliente finalizado.")
        p.terminate()
        p.join()