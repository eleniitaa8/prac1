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
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dir_name = 'insult_service' if service == 'insult' else 'insult_filter'
    script = os.path.join(root_dir, 'xmlrpc_impl', dir_name, 'service.py')
    return subprocess.Popen(
        [python, script, '--port', str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def worker_task(args):
    """
    Ejecuta un lote de n_requests de forma secuencial contra los puertos y cuenta errores.
    Devuelve (elapsed_time, error_count).
    """
    service, ports, n_requests = args
    proxies = [ServerProxy(f'http://localhost:{p}', allow_none=True) for p in ports]
    errors = 0
    start = time.time()
    for i in range(n_requests):
        # Generar texto según servicio
        if service == 'insult':
            text = ''.join(random.choices(string.ascii_lowercase, k=8))
        else:
            text = 'badword ' + ''.join(random.choices(string.ascii_lowercase, k=16))
        proxy = proxies[i % len(proxies)]
        try:
            if service == 'insult':
                proxy.add_insult(text)
            else:
                proxy.add_text(text)
        except ConnectionRefusedError:
            errors += 1
        except Exception:
            errors += 1
    elapsed = time.time() - start
    return elapsed, errors


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

    # Determinar puertos según servicio
    base_port = 8000 if args.service == 'insult' else 8010
    ports = [base_port + i for i in range(args.nodes)]

    # Arrancar réplicas
    processes = [start_service(args.service, p) for p in ports]
    # Dar tiempo a que levanten
    time.sleep(3)

    # Verificar conectividad
    for p in ports:
        proxy = ServerProxy(f'http://localhost:{p}', allow_none=True)
        try:
            if args.service == 'insult':
                proxy.get_insults()
            else:
                proxy.get_results()
        except Exception as e:
            print(f"ERROR: servicio en puerto {p} no responde: {e}")
            sys.exit(1)
    print("All nodes are up and responding")

    # Preparar tareas
    per_worker = args.requests // args.concurrency
    tasks = [(args.service, ports, per_worker) for _ in range(args.concurrency)]

    # Ejecutar benchmark concurrente
    all_times = []
    all_errors = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker_task, task) for task in tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Workers finished"):
            elapsed, errs = future.result()
            all_times.append(elapsed)
            all_errors.append(errs)

    total_requests = per_worker * args.concurrency
    max_time = max(all_times)
    total_errors = sum(all_errors)
    total_success = total_requests - total_errors
    throughput = total_success / max_time if max_time > 0 else 0.0

    print(
        f"Service={args.service} mode={args.mode} nodes={args.nodes} "
        f"requests={total_requests} conc={args.concurrency} -> "
        f"{throughput:.2f} req/s ({total_success}/{total_requests} succeeded, {total_errors} errors)"
    )

    # Cleanup
    for p in processes:
        p.terminate()
