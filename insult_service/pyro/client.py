import Pyro4

# Lookup the service using the PyRO naming convention.
insult_service = Pyro4.Proxy("PYRONAME:InsultService")
print("Adding insult:", insult_service.add_insult("Caca"))
print("Current insults:", insult_service.get_insults())
