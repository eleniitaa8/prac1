from xmlrpc.server import SimpleXMLRPCServer
import re

# Predefined list of insults
INSULTS = ["nincompoop", "idiot", "fool"]

class InsultFilter:
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
    server = SimpleXMLRPCServer(("localhost", 9000))
    server.register_instance(InsultFilter())
    print("XMLRPC InsultFilter server running on port 9000...")
    server.serve_forever()
