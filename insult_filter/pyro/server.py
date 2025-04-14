import Pyro4
import re

INSULTS = ["nincompoop", "idiot", "fool"]

@Pyro4.expose
class InsultFilter(object):
    def __init__(self):
        self.results = []

    def filter_text(self, text):
        filtered = text
        for insult in INSULTS:
            filtered = re.sub(insult, "CENSORED", filtered, flags=re.IGNORECASE)
        self.results.append(filtered)
        return filtered

    def get_results(self):
        return self.results

if __name__ == "__main__":
    filter_service = InsultFilter()
    daemon = Pyro4.Daemon()  # Crea el daemon de PyRO
    uri = daemon.register(filter_service, objectId="InsultFilter")
    print("PyRO InsultFilter is ready. URI =", uri)
    
    try:
        # Conecta al Name Server y registra el objeto con el nombre "InsultFilter"
        ns = Pyro4.locateNS()  # busca el Name Server en localhost:9090 (por defecto)
        ns.register("InsultFilter", uri)
        print("InsultFilter registered in the Name Server.")
    except Exception as e:
        print("Error al registrar en el Name Server:", e)
    
    # Inicia el bucle de espera de peticiones
    daemon.requestLoop()
