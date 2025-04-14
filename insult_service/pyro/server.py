import Pyro4
import threading
import time
import random

@Pyro4.expose
class InsultService(object):
    def __init__(self):
        self.insults = set()

    def add_insult(self, insult):
        if insult not in self.insults:
            self.insults.add(insult)
            return True
        return False

    def get_insults(self):
        return list(self.insults)

    def broadcast_insults(self):
        while True:
            if self.insults:
                print("Broadcasting:", random.choice(list(self.insults)))
            time.sleep(5)

if __name__ == '__main__':
    service = InsultService()
    # Start the broadcaster thread.
    threading.Thread(target=service.broadcast_insults, daemon=True).start()
    
    # Create Pyro daemon and register the service.
    daemon = Pyro4.Daemon()  # crea el daemon
    uri = daemon.register(service, objectId="InsultService")
    print("PyRO InsultService is ready. Object URI =", uri)
    
    # Registra el objeto en el Name Server
    try:
        ns = Pyro4.locateNS()  # se conecta al NS en localhost:9090
        ns.register("InsultService", uri)
        print("InsultService registrado en el Name Server.")
    except Exception as e:
        print("Error al registrar en el Name Server:", e)

    # Inicia el bucle de peticiones
    daemon.requestLoop()
