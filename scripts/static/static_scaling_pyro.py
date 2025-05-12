#!/usr/bin/env python3
import csv, subprocess, sys
from pathlib import Path

# 1. Configuración de experimentos estáticos Pyro4
nodes_levels = [1, 2, 3]
concurrency   = 40      # punto de pico en single-node (~1900 req/s)
scale         = 100     # para total_requests = 40 * 100 = 4000
requests_per_run = concurrency * scale  # = 4000

# 2. Rutas
root_dir         = Path(__file__).resolve().parents[2]
benchmark_script = root_dir / 'benchmark' / 'pyro_performance.py'
output_dir       = root_dir / 'output_files'
output_dir.mkdir(exist_ok=True)
output_file      = output_dir / 'pyro_static.csv'

# 3. Ejecutar y parsear
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['nodes', 'throughput_req_per_s', 'speedup'])
    base_thr = None

    for n in nodes_levels:
        print(f"Running static-scaling Pyro4 with {n} node(s): "
              f"concurrency={concurrency}, requests={requests_per_run}")
        cmd = [
            sys.executable, str(benchmark_script),
            '--service', 'insult',
            '--mode',    'static',
            '--nodes',   str(n),
            '--concurrency', str(concurrency),
            '--requests',    str(requests_per_run)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # Para depurar:
        # print("STDOUT:", res.stdout)
        # print("STDERR:", res.stderr)

        # Buscar throughput
        line = next((l for l in res.stdout.splitlines() if 'req/s' in l), None)
        if not line:
            print(f"  ❌ No throughput found for {n} nodes")
            continue

        # Extraer número antes de 'req/s'
        thr = float(line.split('->')[1].split()[0])
        if n == 1:
            base_thr = thr
            speedup = 1.0
        else:
            speedup = thr / base_thr if base_thr else None

        print(f"  → throughput={thr:.2f} req/s, speedup={speedup:.2f}")
        writer.writerow([n, f"{thr:.2f}", f"{speedup:.2f}"])

print("Results written to", output_file)
