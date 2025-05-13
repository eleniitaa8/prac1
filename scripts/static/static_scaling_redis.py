import csv, subprocess, sys
from pathlib import Path

# 1. Configuración de experimentos estáticos para Redis
t_nodes = [1, 2, 3]
concurrency = 800      # concurrencia de clientes
scale = 10           # factor para calcular total_requests = concurrency * scale
drepetitions = 3       # repeticiones por nivel de nodos
total_requests = concurrency * scale

# 2. Rutas
top_dir = Path(__file__).resolve().parents[2]
benchmark_script = top_dir / 'benchmark' / 'redis_performance.py'
output_dir = top_dir / 'output_files'
output_dir.mkdir(exist_ok=True)
output_file = output_dir / 'redis_static.csv'

# 3. Ejecutar benchmark y parsear resultados
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['nodes', 'avg_throughput_req_per_s', 'speedup'])
    base_thr = None

    for n in t_nodes:
        # Para modo static: pool size por nodo = concurrencia total / nodos
        per_node_conc = concurrency // n
        print(f"\n=== Redis Static Scaling: {n} nodo(s) — {drepetitions} repeticiones ===")
        throughputs = []

        for i in range(1, drepetitions + 1):
            print(f"  Repetición {i}/{drepetitions}...", end=' ')
            cmd = [
                sys.executable, str(benchmark_script),
                '--service', 'insult',
                '--mode', 'static',
                '--nodes', str(n),
                '--concurrency', str(concurrency),
                '--requests', str(total_requests),
                '--redis-host', 'localhost',
                '--redis-port', '6379',
                '--max-connections', str(per_node_conc)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Buscar throughput en la salida
            line = next((l for l in result.stdout.splitlines() if 'req/s' in l), None)
            if not line:
                print("❌ fallo al extraer throughput")
                continue
            # Extraer el número tras '->'
            try:
                thr = float(line.split('->')[1].split()[0])
            except Exception:
                print("❌ formato inesperado en línea de throughput")
                continue
            throughputs.append(thr)
            print(f"throughput={thr:.2f} req/s")

        # Calcular promedio robusto (media o mediana)
        if not throughputs:
            avg_thr = 0.0
        else:
            # Usamos la mediana para mitigar outliers
            throughputs.sort()
            mid = len(throughputs) // 2
            if len(throughputs) % 2 == 1:
                avg_thr = throughputs[mid]
            else:
                avg_thr = (throughputs[mid - 1] + throughputs[mid]) / 2

        if n == 1:
            base_throughput = avg_thr
            speedup = 1.0
        else:
            speedup = (avg_thr / base_throughput) if base_throughput and base_throughput > 0 else 0.0

        print(f"→ Promedio para {n} nodo(s): throughput={avg_thr:.2f} req/s, speedup={speedup:.2f}")
        writer.writerow([n, f"{avg_thr:.2f}", f"{speedup:.2f}"])

print(f"\nResultados escritos en {output_file}")
