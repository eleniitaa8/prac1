"""
redis_performance.py: Script de benchmark para medir el rendimiento básico de Redis
Permite modos:
  - 'single': enviar todas las operaciones a una única instancia Redis
  - 'static': repartir operaciones en round-robin entre varias instancias Redis ("shards" estáticos)

Operaciones soportadas:
  - 'insult': escribe cadenas aleatorias en un set 'insults'
  - 'filter': lee el set 'insults' y simula una operación de filtrado reemplazando palabras por 'CENSORED'

Uso:
  python redis_performance.py --service insult --mode single --requests 10000 --concurrency 50
"""
import argparse
import sys
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis

def worker_task(service, ports, host, n_requests, mode):
    # Preparar clientes Redis según modo
    if mode == 'static' and len(ports) > 1:
        clients = [redis.Redis(host=host, port=p, decode_responses=True) for p in ports]
    else:
        clients = [redis.Redis(host=host, port=ports[0], decode_responses=True)]

    errors = 0
    start = time.time()

    # Para modo 'filter', asegurarnos de que hay datos en el set
    if service == 'filter':
        c0 = clients[0]
        if c0.scard('insults') == 0:
            # Prellenar con insultos dummy
            for i in range(100):
                c0.sadd('insults', f'word{i}')

    for i in range(n_requests):
        try:
            r = clients[i % len(clients)]
            if service == 'insult':
                text = ''.join(random.choices(string.ascii_lowercase, k=8))
                r.sadd('insults', text)
            else:  # filter: leer e iterar reemplazando
                insults = r.smembers('insults')
                # generar texto de ejemplo y filtrar
                sample = ' '.join(random.choice(list(insults)) for _ in range(5)) if insults else 'noinsults'
                for ins in insults:
                    sample = sample.replace(ins, 'CENSORED')
        except Exception:
            errors += 1
    elapsed = time.time() - start
    return elapsed, errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Redis performance benchmark: insult vs filter workloads')
    parser.add_argument('--service', choices=['insult', 'filter'], required=True,
                        help='Servicio a probar: insult=escritura en set, filter=lectura+procesado')
    parser.add_argument('--mode', choices=['single', 'static'], required=True,
                        help='Modo single (una instancia) o static (múltiples shards round-robin)')
    parser.add_argument('--nodes', type=int, default=1,
                        help='Número de instancias Redis (solo en static mode)')
    parser.add_argument('--requests', type=int, default=10000,
                        help='Número total de operaciones a enviar')
    parser.add_argument('--concurrency', type=int, default=50,
                        help='Número de hilos/clientes concurrentes')
    parser.add_argument('--redis-host', default='localhost',
                        help='Host de Redis (por defecto: localhost)')
    parser.add_argument('--redis-port', type=int, default=6379,
                        help='Puerto base de Redis (por defecto: 6379)')
    args = parser.parse_args()

    # Calcular lista de puertos
    if args.mode == 'static':
        ports = [args.redis_port + i for i in range(args.nodes)]
    else:
        ports = [args.redis_port]

    # Comprobar conectividad
    for p in ports:
        try:
            r = redis.Redis(host=args.redis_host, port=p, decode_responses=True)
            r.ping()
        except Exception as e:
            print(f"ERROR: Redis en {args.redis_host}:{p} no responde: {e}")
            sys.exit(1)
    print(f"All Redis nodes are up (host={args.redis_host}, ports={ports})")

    # Distribuir trabajo
    per_worker = args.requests // args.concurrency
    tasks = [(args.service, ports, args.redis_host, per_worker, args.mode)
             for _ in range(args.concurrency)]

    all_times = []
    all_errors = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker_task, *t) for t in tasks]
        for future in as_completed(futures):
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