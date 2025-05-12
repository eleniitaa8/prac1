import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


# --------------------------------------------------
# Análisis Single-node (XMLRPC Stress)
# --------------------------------------------------
stress_csv = Path("output_files") / "xmlrpc_stress.csv"
df_stress = pd.read_csv(stress_csv)

# Throughput vs Concurrency (single-node)
plt.figure()
plt.plot(df_stress["concurrency"], df_stress["throughput_req_per_s"], marker='o')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Throughput (peticiones/segundo)")
plt.title("XML-RPC Single-node: Throughput vs Concurrency")
plt.grid(True)
plt.show()

# Errores vs Concurrency (single-node)
plt.figure()
plt.plot(df_stress["concurrency"], df_stress["errors"], marker='x')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Número de errores")
plt.title("XML-RPC Single-node: Errores vs Concurrency")
plt.grid(True)
plt.show()

# Saturación single-node
max_thr = df_stress["throughput_req_per_s"].max()
opt_conc = int(df_stress[df_stress["throughput_req_per_s"] == max_thr]["concurrency"].iloc[0])
first_errors = int(df_stress[df_stress["errors"] > 0]["concurrency"].min())
print(f"Punto de saturación (single-node): {max_thr:.2f} req/s a concurrency = {opt_conc}")
print(f"Umbral de saturación TCP (primer error) single-node: concurrency = {first_errors}")

# --------------------------------------------------
# Análisis Static-scaling (XMLRPC Static)
# --------------------------------------------------
# Cargar datos
df_static = pd.read_csv(Path("output_files") / "xmlrpc_static.csv")

nodes = df_static["nodes"]
thr   = df_static["throughput_req_per_s"]
speed = df_static["speedup"]
ideal = nodes.astype(float)  # speed-up ideal = N

# 1) Throughput por número de nodos (barras)
plt.figure()
plt.bar(nodes, thr, width=0.6)
for x, y in zip(nodes, thr):
    plt.text(x, y + y*0.02, f"{y:.0f}", ha='center')
plt.xlabel("Número de nodos")
plt.ylabel("Throughput (req/s)")
plt.title("XML-RPC Static Scaling: Throughput vs Nodos")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

# 2) Speed-up real vs ideal (barras agrupadas)
x = np.arange(len(nodes))
width = 0.35

plt.figure()
plt.bar(x - width/2, speed, width, label="Speedup real")
plt.bar(x + width/2, ideal, width, label="Speedup ideal")
plt.xticks(x, nodes)
for i in range(len(nodes)):
    plt.text(x[i]-width/2, speed[i] + 0.02, f"{speed[i]:.2f}", ha='center')
    plt.text(x[i]+width/2, ideal[i] + 0.02, f"{ideal[i]:.0f}", ha='center')
plt.xlabel("Número de nodos")
plt.ylabel("Speedup")
plt.title("XML-RPC Static Scaling: Speedup real vs Ideal")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()