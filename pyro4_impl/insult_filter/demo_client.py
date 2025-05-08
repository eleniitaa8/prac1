import Pyro4
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description='Pyro InsultFilterService Demo Client')
    parser.add_argument('--service-host', default='localhost', help='InsultFilterService host')
    parser.add_argument('--service-port', type=int, default=9015, help='InsultFilterService port')
    args = parser.parse_args()

    service_uri = f"PYRO:InsultFilterService@{args.service_host}:{args.service_port}"
    proxy = Pyro4.Proxy(service_uri)
    texts = ['You are an idiot', 'Hello world', 'What a dummy you are']
    for t in texts:
        proxy.add_text(t)
        print("Submitted:", t)
    time.sleep(0.1)
    print("Filtered:", proxy.get_results())

if __name__ == '__main__':
    main()