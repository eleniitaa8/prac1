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
throughput = df_static["throughput_req_per_s"]
speedup    = df_static["speedup"]

# 1) Throughput por número de nodos
plt.figure()
bars = plt.bar(nodes, throughput, width=0.5, color='C0')
for bar in bars:
    h = bar.get_height()
    x = bar.get_x() + bar.get_width() / 2
    plt.text(
        x,           # posición horizontal: centro de la barra
        h * 0.5,     # posición vertical: mitad de la altura
        f"{h:.0f}",  # texto
        ha='center', va='center',
        color='white'
    )
plt.xlabel("Número de nodos")
plt.ylabel("Throughput (req/s)")
plt.title("XML-RPC Static Scaling: Throughput vs Nodos")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(nodes)
plt.xlim(min(nodes) - 0.5, max(nodes) + 0.5)
plt.tight_layout()
plt.show()

# 2) Speed-up real por número de nodos
plt.figure()
bars = plt.bar(nodes, speedup, width=0.5, color='C1')
for bar in bars:
    h = bar.get_height()
    x = bar.get_x() + bar.get_width() / 2
    plt.text(
        x,
        h * 0.5,
        f"{h:.2f}",
        ha='center', va='center',
        color='white'
    )
plt.xlabel("Número de nodos")
plt.ylabel("Speed-up real")
plt.title("XML-RPC Static Scaling: Speed-up real vs Nodos")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(nodes)
plt.xlim(min(nodes) - 0.5, max(nodes) + 0.5)
plt.tight_layout()
plt.show()