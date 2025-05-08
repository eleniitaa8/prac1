import threading
import time
import argparse
import Pyro4

@Pyro4.expose
class CallbackHandler:
    def receive_insult(self, insult):
        print(f"[Broadcast] {insult}", flush=True)
        return True

def run_callback_server(host, port):
    daemon = Pyro4.Daemon(host=host, port=port)
    daemon.register(CallbackHandler(), objectId="CallbackServer")
    print(f"[Callback] listening at PYRO:CallbackServer@{host}:{port}", flush=True)
    daemon.requestLoop()

def main():
    parser = argparse.ArgumentParser(description='Pyro InsultService Subscriber Demo')
    parser.add_argument('--host', default='localhost', help='Host for callback server')
    parser.add_argument('--port', type=int, default=9010, help='Port for callback server')
    parser.add_argument('--service-host', default='localhost', help='InsultService host')
    parser.add_argument('--service-port', type=int, default=9000, help='InsultService port')
    args = parser.parse_args()

    # 1) Arranco el servidor de callbacks en un hilo demonio
    t = threading.Thread(target=run_callback_server, args=(args.host, args.port), daemon=True)
    t.start()
    time.sleep(1)  # le doy tiempo a que empiece

    # 2) Conecto con el InsultService y me suscribo
    service_uri = f"PYRO:InsultService@{args.service_host}:{args.service_port}"
    service = Pyro4.Proxy(service_uri)
    service.subscribe(args.host, args.port)
    print("Subscribed to InsultService!", flush=True)

    # 3) Pruebo a mandar insultos
    for insult in ('idiot', 'dummy', 'fool'):
        ok = service.add_insult(insult)
        print(f"Add '{insult}': {ok}", flush=True)

    print("Current insults:", service.get_insults(), flush=True)

    # 4) Mantengo vivo el hilo para ver tanto el notify inmediato como el envío periódico
    print("Waiting for broadcasts (Ctrl-C to exit)...", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting demo.", flush=True)

if __name__ == '__main__':
    main()