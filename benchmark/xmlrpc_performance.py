# benchmark/xmlrpc_performance.py
import argparse
import subprocess
import time
import random
import string
import os
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
from xmlrpc.client import ServerProxy
from tqdm import tqdm

def start_service(service, port):
    """
    Arranca la instancia XML-RPC correspondiente en el puerto indicado.
    """
    python = sys.executable
    # Calcula la ruta absoluta al script service.py correcto
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if service == 'insult':
        dir_name = 'insult_service'
    else:
        dir_name = 'insult_filter'
    script = os.path.join(root_dir, 'xmlrpc_impl', dir_name, 'service.py')
    # Lanza el servicio en modo silencioso
    return subprocess.Popen(
        [python, script, '--port', str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def worker_task(args):
    """
    Función que ejecuta un lote de n_requests de forma secuencial
    contra uno o varios nodos XML-RPC en round-robin.
    Devuelve el tiempo transcurrido.
    """
    service, ports, n_requests = args
    proxies = [ServerProxy(f'http://localhost:{p}', allow_none=True) for p in ports]
    start = time.time()
    for i in range(n_requests):
        proxy = proxies[i % len(proxies)]
        if service == 'insult':
            # peticiones de add_insult
            text = ''.join(random.choices(string.ascii_lowercase, k=8))
            proxy.add_insult(text)
        else:
            # peticiones de add_text
            text = 'badword ' + ''.join(random.choices(string.ascii_lowercase, k=16))
            proxy.add_text(text)
    return time.time() - start

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Benchmark XML-RPC InsultService / InsultFilterService'
    )
    parser.add_argument('--service', choices=['insult', 'filter'], required=True,
                        help='Qué servicio probar')
    parser.add_argument('--mode', choices=['single', 'static'], required=True,
                        help='Single-node o static-scaling')
    parser.add_argument('--nodes', type=int, default=1,
                        help='Número de réplicas en static mode')
    parser.add_argument('--requests', type=int, default=10000,
                        help='Total de peticiones a enviar')
    parser.add_argument('--concurrency', type=int, default=50,
                        help='Número de hilos/clientes concurrentes')
    args = parser.parse_args()

    # Determinar puertos según modo y servicio
    base_port = 8000 if args.service == 'insult' else 8010
    ports = [base_port + i for i in range(args.nodes)]

    # Levantar réplicas en background
    procs = [start_service(args.service, p) for p in ports]
    time.sleep(3)  # tiempo para que el servidor escuche
    from xmlrpc.client import ServerProxy
    for p in ports:
        proxy = ServerProxy(f'http://localhost:{p}', allow_none=True)
        try:
            if args.service == 'insult':
                proxy.get_insults()
            else:
                proxy.get_results()
        except Exception as e:
            print(f"El servicio en el puerto {p} no responde:", e)
            sys.exit(1)
    print("Todos los nodos arrancados correctamente")

    # Preparar tareas de clientes
    per_worker = args.requests // args.concurrency
    tasks = [(args.service, ports, per_worker) for _ in range(args.concurrency)]

    # Ejecutar clientes concurrentes con feedback visual
    times = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker_task, task) for task in tasks]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Workers finished", unit="thread"):
            times.append(fut.result())

    total_time = max(times)
    throughput = args.requests / total_time

    print(f"Service={args.service} mode={args.mode} nodes={args.nodes} "
          f"requests={args.requests} conc={args.concurrency} -> "
          f"{throughput:.2f} req/s")

    # Cleanup
    for p in procs:
        p.terminate()
