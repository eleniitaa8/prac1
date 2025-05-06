# xmlrpc_impl/insult_filter/client_demo.py
"""
Demo cliente para InsultFilter:
- envía textos y muestra resultados
"""
import xmlrpc.client, time

if __name__ == '__main__':
    proxy = xmlrpc.client.ServerProxy('http://localhost:8010', allow_none=True)
    for t in ['You are an idiot','Hello world','What a dummy you are']:
        proxy.add_text(t)
        print("Submitted:", t)
    time.sleep(0.1)
    print("Filtered:", proxy.get_results())
