# redis_performance.py
import argparse
import sys
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis

def worker_task(service, ports, host, n_requests, mode, max_connections=None):
    # Preparar clientes Redis según modo, usando pool si está configurado
    clients = []
    for p in ports:
        if max_connections:
            pool = redis.ConnectionPool(
                host=host,
                port=p,
                decode_responses=True,
                max_connections=max_connections
            )
            clients.append(redis.Redis(connection_pool=pool))
        else:
            clients.append(redis.Redis(host=host, port=p, decode_responses=True))

    errors = 0
    start = time.time()

    if service == 'filter':
        # Prellenar set si está vacío
        c0 = clients[0]
        if c0.scard('insults') == 0:
            for i in range(100):
                c0.sadd('insults', f'word{i}')

    for i in range(n_requests):
        try:
            # Seleccionar cliente según modo
            r = clients[i % len(clients)]
            if service == 'insult':
                text = ''.join(random.choices(string.ascii_lowercase, k=8))
                r.sadd('insults', text)
            else:
                insults = r.smembers('insults')
                sample = ' '.join(random.choice(list(insults)) for _ in range(5)) if insults else 'noinsults'
                for ins in insults:
                    sample = sample.replace(ins, 'CENSORED')
        except Exception:
            errors += 1
    elapsed = time.time() - start
    return elapsed, errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Redis performance benchmark: insult vs filter workloads'
    )
    parser.add_argument('--service', choices=['insult', 'filter'], required=True,
                        help='Servicio a probar: insult=escritura, filter=lectura+procesado')
    parser.add_argument('--mode', choices=['single', 'static'], required=True,
                        help='Modo single o static (shards round-robin)')
    parser.add_argument('--nodes', type=int, default=1,
                        help='Número de instancias Redis (static mode)')
    parser.add_argument('--requests', type=int, default=10000,
                        help='Total de operaciones a enviar')
    parser.add_argument('--concurrency', type=int, default=50,
                        help='Número de hilos concurrentes')
    parser.add_argument('--redis-host', default='localhost',
                        help='Host de Redis')
    parser.add_argument('--redis-port', type=int, default=6379,
                        help='Puerto base de Redis')
    parser.add_argument('--max-connections', type=int, default=None,
                        help='Máximo de conexiones en el pool por instancia')
    args = parser.parse_args()

    # Lista de puertos según modo
    if args.mode == 'static':
        ports = [args.redis_port + i for i in range(args.nodes)]
    else:
        ports = [args.redis_port]

    # Verificar conectividad
    for p in ports:
        try:
            r = redis.Redis(host=args.redis_host, port=p, decode_responses=True)
            r.ping()
        except Exception as e:
            print(f"ERROR: Redis en {args.redis_host}:{p} no responde: {e}")
            sys.exit(1)
    print(f"All Redis nodes are up (host={args.redis_host}, ports={ports})")

    per_worker = args.requests // args.concurrency
    tasks = [
        (args.service, ports, args.redis_host, per_worker, args.mode, args.max_connections)
        for _ in range(args.concurrency)
    ]

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