import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:8000")
# Add an insult and then retrieve all insults.
print("Adding insult:", proxy.add_insult("You nincompoop!"))
print("Current insults:", proxy.get_insults())
