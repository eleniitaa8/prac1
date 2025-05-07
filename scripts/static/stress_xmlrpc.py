"""
scripts/static/stress_xmlrpc.py
Stress-test single-node XML-RPC InsultService con carga ajustada para tiempos controlados.
Genera un CSV con throughput vs concurrency = número de hilos.
"""
import subprocess
import csv
import sys
from pathlib import Path

# Configuración dinámica: concurrency y scale para ajustar carga
concurrency_levels = [1, 2, 5, 10, 20, 50, 100, 300, 600, 1000]
scale = 20  # número de requests por hilo

benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'xmlrpc_performance.py'
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_file = output_dir / 'xmlrpc_single_node.csv'

# Crear directorio de salida
output_dir.mkdir(parents=True, exist_ok=True)

# Preparar CSV
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['concurrency', 'requests', 'throughput_req_per_s'])

    for conc in concurrency_levels:
        total_requests = conc * scale
        print(f"Running: concurrency={conc}, total_requests={total_requests}")
        cmd = [
            sys.executable, str(benchmark_script),
            '--service', 'insult',
            '--mode', 'single',
            '--requests', str(total_requests),
            '--concurrency', str(conc)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        stdout_lines = proc.stdout.strip().splitlines()
        # Buscar línea con '->'
        thr_line = next((l for l in stdout_lines if '->' in l), None)
        if not stdout_lines:
            err = proc.stderr.strip().replace('\n', ' ')
            print(f"❌ No stdout para concurrency={conc}, stderr: {err}")
            throughput = 0.0
        elif thr_line is None:
            err = proc.stderr.strip().replace('\n', ' ')
            print(f"❌ No encontré línea de throughput para concurrency={conc}, stdout: {stdout_lines}, stderr: {err}")
            throughput = 0.0
        else:
            try:
                # parsear '-> XX.XX req/s'
                part = thr_line.split('->')[1]
                throughput = float(part.strip().split()[0])
            except Exception as e:
                print(f"❌ No pude parsear throughput de '{thr_line}': {e}")
                throughput = 0.0

        writer.writerow([conc, total_requests, throughput])
        print(f" -> {throughput} req/s")

print(f"Results written to {output_file}")