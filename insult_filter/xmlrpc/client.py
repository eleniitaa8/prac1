import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:9000")
text = "You nincompoop, you idiot!"
result = proxy.filter_text(text)
print("Filtered text:", result)
print("All filtered results:", proxy.get_results())
