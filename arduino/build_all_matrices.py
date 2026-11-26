import numpy as np
import pandas as pd

data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16)

COUNTER_COUNT = 13

counters = (data[:, 0] >> 12) & 0x0F
adc = data & 0x03FF

cycles = min(np.count_nonzero(counters == c) for c in range(COUNTER_COUNT))

groups = np.array([
    adc[counters == c][:cycles]
    for c in range(COUNTER_COUNT)
])

for sample in range(16):

    matrix = groups[:, :, sample].T

    df = pd.DataFrame(
        matrix,
        columns=[f"Counter {i}" for i in range(COUNTER_COUNT)],
        index=[f"Cycle {i + 1}" for i in range(cycles)]
    )

    print(f"\n{'=' * 30}")
    print(f"Sample {sample + 1} | Shape: {matrix.shape}")
    print(f"{'=' * 30}\n")

    print(df.to_string())