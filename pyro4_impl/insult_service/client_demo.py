import Pyro4, multiprocessing, time

@Pyro4.expose
class CallbackHandler:
    def receive_insult(self, insult):
        print(f"[Broadcast] {insult}")
        return True


def run_callback_server(host, port):
    daemon = Pyro4.Daemon(host=host, port=port)
    daemon.register(CallbackHandler(), objectId="CallbackServer")
    print(f"[Callback] listening at PYRO:CallbackServer@{host}:{port}")
    daemon.requestLoop()

if __name__ == '__main__':
    HOST, PORT = 'localhost', 9010
    p = multiprocessing.Process(target=run_callback_server, args=(HOST, PORT))
    p.start()
    time.sleep(1)

    service = Pyro4.Proxy("PYRO:InsultService@localhost:9000")
    service.subscribe(f"PYRO:CallbackServer@{HOST}:{PORT}")

    for insult in ('idiot', 'dummy', 'fool'):
        print(f"Add '{insult}':", service.add_insult(insult))

    print("Current insults:", service.get_insults())
    try:
        p.join()
    except KeyboardInterrupt:
        p.terminate()
        p.join()