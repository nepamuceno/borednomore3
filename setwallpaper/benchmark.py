#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# Carpeta de frames
frames_dir = "/tmp/bnm3_frames"

# Detectar automáticamente todos los frames disponibles
frames = sorted(
    os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".jpg")
)

num_frames = len(frames)
print(f"Se encontraron {num_frames} frames")

# Leer número de repeticiones desde argumento
if len(sys.argv) > 1:
    try:
        REPS = int(sys.argv[1])
    except ValueError:
        print("El argumento debe ser un número entero")
        sys.exit(1)
else:
    REPS = 5  # valor por defecto

total_time = 0.0

for rep in range(1, REPS + 1):
    print(f"\nRepetición {rep}:")
    start = time.time()
    for frame in frames:
        subprocess.run(["./setwallpaper", frame], check=True)
    end = time.time()
    elapsed = end - start
    total_time += elapsed
    avg_per_frame = elapsed / num_frames
    print(f"Tiempo total: {elapsed:.4f} segundos")
    print(f"Tiempo promedio por frame: {avg_per_frame:.4f} segundos")

print("\n=== Resumen final ===")
print(f"Repeticiones: {REPS}")
print(f"Frames por repetición: {num_frames}")
print(f"Total de frames aplicados: {REPS * num_frames}")
print(f"Tiempo acumulado total: {total_time:.4f} segundos")
print(f"Tiempo promedio por frame (global): {total_time / (REPS * num_frames):.4f} segundos")
