import subprocess
import csv
import sys
import re
from pathlib import Path

concurrency_levels = [10, 500, 1000, 1050, 1100, 1200, 1500]
scale = 20
benchmark_script = Path(__file__).resolve().parents[2] / 'benchmark' / 'pyro_performance.py'
output_dir = Path(__file__).resolve().parents[2] / 'output_files'
output_file = output_dir / 'pyro_single_node.csv'
output_dir.mkdir(parents=True, exist_ok=True)

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
        result_line = next((l for l in stdout_lines if 'req/s' in l), None)
        if not result_line:
            err = proc.stderr.strip().replace('\n', ' ')
            print(f"❌ No encontré resultado para concurrency={conc}, stderr: {err}")
            throughput, succeeded, errors = 0.0, 0, total_requests
        else:
            m = re.search(r'->\s*([\d\.]+)\s*req/s\s*\((\d+)/(\d+) succeeded,\s*(\d+) errors\)', result_line)
            if m:
                throughput = float(m.group(1)); succeeded = int(m.group(2)); errors = int(m.group(4))
            else:
                try: throughput = float(result_line.split('->')[1].strip().split()[0])
                except: throughput = 0.0
                succeeded, errors = total_requests, 0
        print(f" -> {throughput:.2f} req/s, succeeded={succeeded}, errors={errors}")
        writer.writerow([conc, total_requests, throughput, succeeded, errors])

print(f"Results written to {output_file}")
