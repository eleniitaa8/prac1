import Pyro4
import multiprocessing, time, random

@Pyro4.expose
class InsultService:
    def __init__(self, insults, subscribers):
        self.insults = insults        # Manager().list()
        self.subscribers = subscribers

    def add_insult(self, text):
        if text not in self.insults:
            self.insults.append(text)
            return True
        return False

    def get_insults(self):
        return list(self.insults)

    def subscribe(self, callback_uri):
        if callback_uri not in self.subscribers:
            self.subscribers.append(callback_uri)
        return True

    def _broadcaster(self):
        while True:
            time.sleep(5)
            if not self.insults or not self.subscribers:
                continue
            insult = random.choice(self.insults)
            for uri in list(self.subscribers):
                try:
                    cb = Pyro4.Proxy(uri)
                    cb.receive_insult(insult)
                except:
                    continue

def main():
    mgr = multiprocessing.Manager()
    insults = mgr.list()
    subscribers = mgr.list()

    daemon = Pyro4.Daemon(host="0.0.0.0", port=9000)
    uri = daemon.register(InsultService(insults, subscribers), objectId="InsultService")
    print(f"[InsultService] URI: {uri}")

    # broadcaster
    service = InsultService(insults, subscribers)
    p = multiprocessing.Process(target=service._broadcaster)
    p.start()

    daemon.requestLoop()

if __name__ == '__main__':
    main()