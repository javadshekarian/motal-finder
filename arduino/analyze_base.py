
import numpy as np

data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16)

PERIOD = 13

for i in range(PERIOD):
    group = data[i::PERIOD]

    print(f"\nWaves: {i+1}, {i+1+PERIOD}, ...")
    print("Sample | Mean | StdDev | Min | Max")

    for j in range(16):
        col = group[:, j]
        print(f"{j+1:6} | {np.mean(col):7.2f} | {np.std(col):7.4f} | {np.min(col):4} | {np.max(col):4}")
