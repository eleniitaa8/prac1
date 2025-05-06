import Pyro4, time

if __name__ == '__main__':
    proxy = Pyro4.Proxy("PYRO:InsultFilterService@localhost:9015")
    texts = ['You are an idiot', 'Hello world', 'What a dummy you are']
    for t in texts:
        proxy.add_text(t)
        print("Submitted:", t)
    time.sleep(0.1)
    print("Filtered:", proxy.get_results())