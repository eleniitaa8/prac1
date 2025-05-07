import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

csv_path = Path(__file__).resolve().parents[2] / 'output_files' / 'xmlrpc_single_node.csv'
df = pd.read_csv(csv_path)

# Generar gráfico de Throughput vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["throughput_req_per_s"], marker='o')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Throughput (peticiones/segundo)")
plt.title("XML-RPC Single-node: Throughput vs Concurrency")
plt.grid(True)
plt.show()

# Calcular el punto de saturación (máximo throughput y concurrencia mínima)
max_thr = df["throughput_req_per_s"].max()
opt_conc = df[df["throughput_req_per_s"] == max_thr]["concurrency"].min()
print(f"Punto de saturación: throughput máximo ≈ {max_thr:.2f} req/s alcanzado con concurrency = {opt_conc}")