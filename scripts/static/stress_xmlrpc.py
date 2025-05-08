"""
scripts/static/stress_xmlrpc.py
Stress-test single-node XML-RPC InsultService con detalle de errores.
Genera un CSV con throughput, aciertos y errores por nivel de concurrency.
"""
import subprocess
import csv
import sys
import re
from pathlib import Path

# Configuración dinámica: concurrency y scale para ajustar carga
concurrency_levels = [1, 100, 250, 500, 1000, 1200, 1500, 2000]
scale = 20  # número de requests por hilo

benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'xmlrpc_performance.py'
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_file = output_dir / 'xmlrpc_single_node.csv'

# Crear directorio de salida
output_dir.mkdir(parents=True, exist_ok=True)

# Preparar CSV con cabecera ampliada
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['concurrency', 'requests', 'throughput_req_per_s', 'succeeded', 'errors'])

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

        # Buscar la línea con 'req/s'
        result_line = next((l for l in stdout_lines if 'req/s' in l), None)
        if not result_line:
            err = proc.stderr.strip().replace('\n', ' ')
            print(f"❌ No encontré resultado para concurrency={conc}, stderr: {err}")
            throughput = 0.0
            succeeded = 0
            errors = total_requests
        else:
            # Intentar extraer throughput, succeeded y errores
            m = re.search(r'->\s*([\d\.]+)\s*req/s\s*\((\d+)/(\d+) succeeded,\s*(\d+) errors\)', result_line)
            if m:
                throughput = float(m.group(1))
                succeeded = int(m.group(2))
                # total = int(m.group(3))  # debe coincidir con total_requests
                errors = int(m.group(4))
            else:
                # Fallback: solo throughput sin detalle
                try:
                    part = result_line.split('->')[1]
                    throughput = float(part.strip().split()[0])
                except:
                    throughput = 0.0
                succeeded = total_requests
                errors = 0
        # Imprimir info detallada
        print(f" -> {throughput:.2f} req/s, succeeded={succeeded}, errors={errors}")
        # Guardar en CSV
        writer.writerow([conc, total_requests, throughput, succeeded, errors])

print(f"Results written to {output_file}")