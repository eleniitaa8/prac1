# prueba.py
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
# Llama a add_insult con un texto de prueba
ok = proxy.add_insult('test_insult')
print('add_insult returned:', ok)
# Recupera la lista de insultos
lista = proxy.get_insults()
print('get_insults returned:', lista)