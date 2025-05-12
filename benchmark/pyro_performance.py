import argparse
import subprocess
import time
import random
import string
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import Pyro4

import gc
gc.disable()
gc.collect()

# ProxyManager para modos "single" (no usado en "static")
# Mecanismo de reintentos con back-off exponencial: 
#   - max_retries: número máximo de reintentos
#   - base_backoff: tiempo base para el back-off exponencial
#   - failure_threshold: número de fallos antes de marcar el proxy como muerto
#   - ping_latency: mide la latencia de un proxy para balanceo de carga
#   - weighted_choice: elige un proxy basado en latencias
# --------------------------------------
class ProxyManager:
    def __init__(self, uris, max_retries=3, base_backoff=0.05, failure_threshold=5):
        self.wrappers = [ProxyWrapper(uri, max_retries, base_backoff) for uri in uris]
        self.failure_threshold = failure_threshold

    def get_live_proxies(self):
        return [w for w in self.wrappers if w.failures < self.failure_threshold]

    def weighted_choice(self):
        live = self.get_live_proxies()
        if len(live) == 1:
            return live[0]
        latencies = [w.ping_latency() for w in live]
        weights = [1.0 / (lat or 0.001) for lat in latencies]
        return random.choices(live, weights)[0]

class ProxyWrapper:
    def __init__(self, uri, max_retries, base_backoff):
        self.uri = uri
        self.proxy = Pyro4.Proxy(uri)
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.failures = 0

    def call(self, method, *args):
        for attempt in range(self.max_retries):
            try:
                return getattr(self.proxy, method)(*args)
            except Exception:
                time.sleep(self.base_backoff * (2 ** attempt))
        self.failures += 1
        raise

    def ping_latency(self):
        start = time.time()
        try:
            self.proxy.get_insults()
            return time.time() - start
        except:
            return float('inf')
# --------------------------------------

def start_service(service, port):
    python = sys.executable
    module = 'pyro4_impl.insult_service.service' if service == 'insult' \
             else 'pyro4_impl.insult_filter.service'
    cmd = [
        python, '-m', module,
        '--port', str(port),
        '--redis-host', 'localhost',
        '--redis-port', '6379'
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def worker_task(args):
    service, ports, n_requests, mode = args

    if mode == 'static':
        # simple round-robin, sin medir latencias
        proxies = [
            Pyro4.Proxy(f"PYRO:{'InsultService' if service=='insult' else 'InsultFilterService'}@localhost:{p}")
            for p in ports
        ]
        errors = 0
        start = time.time()
        for i in range(n_requests):
            if service == 'insult':
                text = ''.join(random.choices(string.ascii_lowercase, k=8))
                try:
                    proxies[i % len(proxies)].add_insult(text)
                except:
                    errors += 1
            else:
                text = 'badword ' + ''.join(random.choices(string.ascii_lowercase, k=16))
                try:
                    proxies[i % len(proxies)].add_text(text)
                except:
                    errors += 1
        return time.time() - start, errors

    # modo "single" o cualquier otro: usa ProxyManager con back-off
    uris = [
        f"PYRO:{'InsultService' if service=='insult' else 'InsultFilterService'}@localhost:{p}"
        for p in ports
    ]
    mgr = ProxyManager(uris, max_retries=2, base_backoff=0.01, failure_threshold=10)
    errors = 0
    start = time.time()
    for _ in range(n_requests):
        try:
            wrapper = mgr.weighted_choice()
            if service == 'insult':
                text = ''.join(random.choices(string.ascii_lowercase, k=8))
                wrapper.call('add_insult', text)
            else:
                text = 'badword ' + ''.join(random.choices(string.ascii_lowercase, k=16))
                wrapper.call('add_text', text)
        except:
            errors += 1
    return time.time() - start, errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark Pyro InsultService / InsultFilterService')
    parser.add_argument('--service', choices=['insult', 'filter'], required=True,
                        help='Qué servicio probar')
    parser.add_argument('--mode', choices=['single', 'static'], required=True,
                        help='Single-node o static-scaling')
    parser.add_argument('--nodes', type=int, default=1,
                        help='Número de réplicas (solo en static mode)')
    parser.add_argument('--requests', type=int, default=10000,
                        help='Total de peticiones a enviar')
    parser.add_argument('--concurrency', type=int, default=50,
                        help='Número de hilos/clientes concurrentes')
    args = parser.parse_args()

    base_port = 9000 if args.service == 'insult' else 9015
    ports = [base_port + i for i in range(args.nodes)]

    # Arrancar réplicas
    processes = [start_service(args.service, p) for p in ports]
    time.sleep(3)

    # Verificar conectividad
    for p in ports:
        proxy = Pyro4.Proxy(f"PYRO:{'InsultService' if args.service=='insult' else 'InsultFilterService'}@localhost:{p}")
        try:
            if args.service == 'insult':
                proxy.get_insults()
            else:
                proxy.get_results()
        except Exception as e:
            print(f"ERROR: servicio en puerto {p} no responde: {e}")
            sys.exit(1)
    print("All nodes are up and responding")

    per_worker = args.requests // args.concurrency
    tasks = [(args.service, ports, per_worker, args.mode) for _ in range(args.concurrency)]

    all_times, all_errors = [], []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker_task, task) for task in tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Workers finished"):
            elapsed, errs = future.result()
            all_times.append(elapsed)
            all_errors.append(errs)

    total_requests = per_worker * args.concurrency
    max_time = max(all_times) if all_times else 0
    total_errors = sum(all_errors)
    total_success = total_requests - total_errors
    throughput = total_success / max_time if max_time > 0 else 0.0

    print(
        f"Service={args.service} mode={args.mode} nodes={args.nodes} "
        f"requests={total_requests} conc={args.concurrency} -> "
        f"{throughput:.2f} req/s ({total_success}/{total_requests} succeeded, {total_errors} errors)"
    )

    for p in processes:
        p.terminate()