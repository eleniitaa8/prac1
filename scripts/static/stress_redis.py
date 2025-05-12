import subprocess
import csv
import sys
import re
from pathlib import Path

# Niveles de concurrencia a probar\ 
concurrency_levels = [100, 500, 1000, 1250, 1500]
# Número de peticiones por hilo\ 
scale = 100

# Ruta al script de benchmark de Redis
benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'redis_performance.py'
# Carpeta y fichero de salida
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_file = output_dir / 'redis_stress.csv'
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['concurrency', 'requests', 'throughput_req_per_s', 'succeeded', 'errors'])

    for conc in concurrency_levels:
        total_requests = conc * scale
        print(f"Running: concurrency={conc}, total_requests={total_requests}")

        cmd = [
            sys.executable,
            str(benchmark_script),
            '--service', 'insult',
            '--mode', 'single',
            '--requests', str(total_requests),
            '--concurrency', str(conc)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        stdout_lines = proc.stdout.strip().splitlines()
        # Buscar la línea de resultado que contenga 'req/s'
        result_line = next((l for l in stdout_lines if 'req/s' in l), None)

        if not result_line:
            err = proc.stderr.strip().replace('\n', ' ')
            print(f"❌ No encontré resultado para concurrency={conc}, stderr: {err}")
            throughput, succeeded, errors = 0.0, 0, total_requests
        else:
            # Ejemplo de línea: "... -> 422.40 req/s (5/5 succeeded, 0 errors)"
            m = re.search(
                r'->\s*([\d\.]+)\s*req/s\s*\((\d+)/(\d+) succeeded,\s*(\d+) errors\)',
                result_line
            )
            if m:
                throughput = float(m.group(1))
                succeeded = int(m.group(2))
                errors = int(m.group(4))
            else:
                # Fallback: extraer el primer número tras '->'
                try:
                    throughput = float(result_line.split('->')[1].strip().split()[0])
                except Exception:
                    throughput = 0.0
                succeeded, errors = total_requests, 0

        print(f" -> {throughput:.2f} req/s, succeeded={succeeded}, errors={errors}")
        writer.writerow([conc, total_requests, throughput, succeeded, errors])

print(f"Results written to {output_file}")
