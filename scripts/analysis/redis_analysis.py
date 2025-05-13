import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Cargar datos
csv_path = Path("output_files") / "redis_stress.csv"
df = pd.read_csv(csv_path)

# Gráfico 1: Throughput medio vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["avg_throughput_req_per_s"], marker='o')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Throughput medio (peticiones/segundo)")
plt.title("Redis Single-node: Throughput medio vs Concurrency")
plt.grid(True)
plt.show()

# Gráfico 2: Errores medios vs Concurrency
plt.figure()
plt.plot(df["concurrency"], df["avg_errors"], marker='x')
plt.xlabel("Concurrency (hilos clientes)")
plt.ylabel("Errores medios")
plt.title("Redis Single-node: Errores medios vs Concurrency")
plt.grid(True)
plt.show()

# Punto de saturación basado en throughput máximo antes de caída
max_thr = df["avg_throughput_req_per_s"].max()
opt_conc = int(df.loc[df["avg_throughput_req_per_s"].idxmax(), "concurrency"])
print(f"Punto de saturación: throughput máximo ≈ {max_thr:.2f} req/s en concurrency = {opt_conc}")

# Punto donde errores empiezan a aparecer
if (df["avg_errors"] > 0).any():
    first_errors = int(df.loc[df["avg_errors"] > 0, "concurrency"].min())
    print(f"Umbral de saturación TCP (primer error) en concurrency = {first_errors}")
else:
    print("No se registraron errores en ningún nivel de concurrencia")