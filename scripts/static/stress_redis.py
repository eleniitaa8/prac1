import subprocess
import csv
import sys
import re
from pathlib import Path

# Niveles de concurrencia a probar 
concurrency_levels = [100, 250, 500, 750, 1000, 1100, 1200]
# Número de peticiones por hilo 
scale = 20
# Número de repeticiones para cada nivel de concurrencia
repetitions = 3

# Ruta al script de benchmark de Redis
benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'redis_performance.py'
# Carpeta y fichero de salida
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_file = output_dir / 'redis_stress.csv'
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['concurrency', 'requests', 'pool_size', 'avg_throughput_req_per_s', 'avg_succeeded', 'avg_errors'])

    for conc in concurrency_levels:
        total_requests = conc * scale
        pool_size = conc  # ajustamos el pool igual al número de hilos
        throughputs = []
        successes = []
        errors_list = []

        print(f"\nTesting concurrency={conc}, total_requests={total_requests}, pool_size={pool_size}")
        for i in range(repetitions):
            print(f" Run {i+1}/{repetitions}...", end='')
            cmd = [
                sys.executable,
                str(benchmark_script),
                '--service', 'insult',
                '--mode', 'single',
                '--requests', str(total_requests),
                '--concurrency', str(conc),
                '--max-connections', str(pool_size),  # parámetro de pool
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            stdout_lines = proc.stdout.strip().splitlines()
            result_line = next((l for l in stdout_lines if 'req/s' in l), None)

            if not result_line:
                err = proc.stderr.strip().replace('\n', ' ')
                print(f" ❌ no result, stderr: {err}")
                tp = 0.0
                succ = 0
                err_cnt = total_requests
            else:
                m = re.search(
                    r'->\s*([\d\.]+)\s*req/s\s*\((\d+)/(\d+) succeeded,\s*(\d+) errors\)',
                    result_line
                )
                if m:
                    tp = float(m.group(1))
                    succ = int(m.group(2))
                    err_cnt = int(m.group(4))
                else:
                    try:
                        tp = float(result_line.split('->')[1].strip().split()[0])
                    except:
                        tp = 0.0
                    succ = total_requests
                    err_cnt = 0
                print(f" {tp:.2f} req/s, succ={succ}, err={err_cnt}")

            throughputs.append(tp)
            successes.append(succ)
            errors_list.append(err_cnt)

        # Cálculo de medias
        avg_tp = sum(throughputs) / repetitions
        avg_succ = sum(successes) // repetitions
        avg_err = sum(errors_list) // repetitions
        print(f" Avg -> {avg_tp:.2f} req/s, succ={avg_succ}, err={avg_err}")

        writer.writerow([conc, total_requests, pool_size, f"{avg_tp:.2f}", avg_succ, avg_err])

print(f"\nResults written to {output_file}")