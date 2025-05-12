#!/usr/bin/env python3
import csv, subprocess, sys
from pathlib import Path

# 1. Configuración de experimentos estáticos Pyro4
nodes_levels = [1, 2, 3]
concurrency   = 40      # punto de pico en single-node (~1900 req/s)
scale         = 100     # para total_requests = 40 * 100 = 4000
requests_per_run = concurrency * scale  # = 4000
repetitions = 3

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
        throughputs = []
        print(f"\n=== Nodo(s) = {n} — {repetitions} repeticiones ===")
        for i in range(1, repetitions + 1):
            print(f"  Repetición {i}/{repetitions}...", end=' ')
            cmd = [
                sys.executable, str(benchmark_script),
                '--service',      'insult',
                '--mode',         'static',
                '--nodes',        str(n),
                '--concurrency',  str(concurrency),
                '--requests',     str(requests_per_run)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Buscar la línea con 'req/s'
            line = next((l for l in result.stdout.splitlines() if 'req/s' in l), None)
            if not line:
                print("❌ fallo al extraer throughput")
                continue
            thr = float(line.split('->')[1].split()[0])
            throughputs.append(thr)
            print(f"throughput={thr:.2f} req/s")

        if not throughputs:
            avg_thr = 0.0
        else:
            avg_thr = sum(throughputs) / len(throughputs)
        if n == 1:
            base_thr = avg_thr
            speedup = 1.0
        else:
            speedup = avg_thr / base_thr if base_thr and base_thr > 0 else 0.0

        print(f"→ Promedio para {n} nodos: throughput={avg_thr:.2f} req/s, speedup={speedup:.2f}")
        writer.writerow([n, f"{avg_thr:.2f}", f"{speedup:.2f}"])

print(f"\nResultados escritos en {output_file}")