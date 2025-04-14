from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
import random

class InsultService:
    def __init__(self):
        # Use a set for fast lookup and to avoid duplicates.
        self.insults = set()

    def add_insult(self, insult):
        if insult not in self.insults:
            self.insults.add(insult)
            return True
        return False

    def get_insults(self):
        # Convert to list for XMLRPC compatibility.
        return list(self.insults)

    def broadcast_insults(self):
        while True:
            if self.insults:
                # Pick a random insult to "broadcast"
                print("Broadcasting:", random.choice(list(self.insults)))
            time.sleep(5)

if __name__ == "__main__":
    service = InsultService()
    # Start the broadcaster thread.
    threading.Thread(target=service.broadcast_insults, daemon=True).start()
    server = SimpleXMLRPCServer(("localhost", 8000))
    server.register_instance(service)
    print("XMLRPC InsultService server running on port 8000...")
    server.serve_forever()
