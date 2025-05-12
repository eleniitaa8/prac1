import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Cargar datos
csv_path = Path("output_files") / "pyro_stress.csv"
df = pd.read_csv(csv_path)

# Gráfico 1: Throughput vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["throughput_req_per_s"], marker='o')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Throughput (peticiones/segundo)")
plt.title("Pyro4 Single-node: Throughput vs Concurrency")
plt.grid(True)
plt.show()

# Gráfico 2: Errores vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["errors"], marker='x')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Número de errores (ConnectionRefusedError)")
plt.title("Pyro4 Single-node: Errores vs Concurrency")
plt.grid(True)
plt.show()

# Punto de saturación basado en throughput máximo antes de caída
max_thr = df["throughput_req_per_s"].max()
opt_conc = int(df[df["throughput_req_per_s"] == max_thr]["concurrency"].min())
print(f"Punto de saturación: throughput máximo ≈ {max_thr:.2f} req/s en concurrency = {opt_conc}")

# Punto donde errores empiezan a aparecer
first_errors = df[df["errors"] > 0]["concurrency"].min()
print(f"Umbral de saturación TCP (primer error) en concurrency = {first_errors}")

# --------------------------------------------------
# Análisis Static-scaling (Pyro4)
# --------------------------------------------------

# Cargar datos
df_static = pd.read_csv(Path("output_files") / "pyro_static.csv")

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
plt.title("Pyro4 Static Scaling: Throughput vs Nodos")
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
plt.title("Pyro4 Static Scaling: Speed-up real vs Nodos")
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(nodes)
plt.xlim(min(nodes) - 0.5, max(nodes) + 0.5)
plt.tight_layout()
plt.show()