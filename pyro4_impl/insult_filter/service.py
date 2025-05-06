import Pyro4, multiprocessing

@Pyro4.expose
class InsultFilterService:
    def __init__(self, insult_service_uri, results):
        self.insult_url = insult_service_uri
        self.results = results  # Manager().list()
        self.insults_cache = None

    def _load_insults(self):
        svc = Pyro4.Proxy(self.insult_url)
        self.insults_cache = svc.get_insults()

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
    uri_insult = "PYRO:InsultService@localhost:9000"

    daemon = Pyro4.Daemon(host="0.0.0.0", port=9015)
    uri = daemon.register(InsultFilterService(uri_insult, results),
                           objectId="InsultFilterService")
    print(f"[InsultFilter] URI: {uri}")

    daemon.requestLoop()

if __name__ == '__main__':
    main()