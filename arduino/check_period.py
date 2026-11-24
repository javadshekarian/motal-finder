import numpy as np

data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16).astype(np.int32)

for j in range(16):
    x = data[:, j]
    period_errors = np.abs(x[13:] - x[:-13])

    print(f"Sample {j+1:2}: Mean error={np.mean(period_errors):.3f}, Max error={np.max(period_errors)}")