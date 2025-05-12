import csv
import subprocess
import sys
from pathlib import Path

# Configuración de experimentos estáticos XML-RPC
nodes_levels = [1, 2, 3]
# Basado en el stress test single-node, la mejor concurrency es 1000 hilos
concurrency = 1000
# Usamos el mismo 'scale' de 20 requests por hilo para el total de trabajo
scale = 20
requests_per_run = concurrency * scale

# Rutas
benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'xmlrpc_performance.py'
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_dir.mkdir(exist_ok=True)
output_file = output_dir / 'xmlrpc_static.csv'

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['nodes', 'throughput_req_per_s', 'speedup'])
    base_throughput = None

    for n in nodes_levels:
        print(f"Ejecutando static-scaling con {n} nodos, concurrency={concurrency}, requests={requests_per_run}")
        cmd = [
            sys.executable, str(benchmark_script),
            '--service', 'insult',
            '--mode', 'static',
            '--nodes', str(n),
            '--concurrency', str(concurrency),
            '--requests', str(requests_per_run)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        stdout_lines = result.stdout.strip().splitlines()
        # Extraer la línea con 'req/s'
        line = next((l for l in stdout_lines if 'req/s' in l), None)
        if not line:
            print(f"ERROR: no se encontró throughput para nodos={n}")
            continue
        # Parsear throughput
        # Ej: " -> 313.37 req/s (..."
        throughput = float(line.split('->')[1].split()[0])
        if n == 1:
            base_throughput = throughput
            speedup = 1.0
        else:
            speedup = throughput / base_throughput
        writer.writerow([n, f"{throughput:.2f}", f"{speedup:.2f}"])

print(f"Resultados escritos en {output_file}")