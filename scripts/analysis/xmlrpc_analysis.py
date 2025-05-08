import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Cargar datos
csv_path = Path("output_files") / "xmlrpc_single_node.csv"
df = pd.read_csv(csv_path)

# Gráfico 1: Throughput vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["throughput_req_per_s"], marker='o')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Throughput (peticiones/segundo)")
plt.title("XML-RPC Single-node: Throughput vs Concurrency")
plt.grid(True)
plt.show()

# Gráfico 2: Errores vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["errors"], marker='x')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Número de errores (ConnectionRefusedError)")
plt.title("XML-RPC Single-node: Errores vs Concurrency")
plt.grid(True)
plt.show()

# Punto de saturación basado en throughput máximo antes de caída
max_thr = df["throughput_req_per_s"].max()
opt_conc = int(df[df["throughput_req_per_s"] == max_thr]["concurrency"].min())
print(f"Punto de saturación: throughput máximo ≈ {max_thr:.2f} req/s en concurrency = {opt_conc}")

# Punto donde errores empiezan a aparecer
first_errors = df[df["errors"] > 0]["concurrency"].min()
print(f"Umbral de saturación TCP (primer error) en concurrency = {first_errors}")