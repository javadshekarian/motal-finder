
import numpy as np
import pandas as pd

data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16)

GROUP_SIZE = 13
group_count = len(data) // GROUP_SIZE

groups = data[:group_count * GROUP_SIZE].reshape(
    group_count,
    GROUP_SIZE,
    16
)

# Calculate baseline mean
BASE_MEAN = np.mean(groups, axis=0)

# Calculate deviations from the mean
differences = groups - BASE_MEAN

# Calculate maximum and minimum noise
MAX_NOISE = np.max(differences, axis=0)
MIN_NOISE = np.min(differences, axis=0)

# Display matrices
matrices = {
    "BASE_MEAN": BASE_MEAN,
    "MAX_NOISE": MAX_NOISE,
    "MIN_NOISE": MIN_NOISE
}

for name, matrix in matrices.items():
    df = pd.DataFrame(
        matrix,
        index=[f"Position {i+1}" for i in range(GROUP_SIZE)],
        columns=[f"Sample {i+1}" for i in range(16)]
    )

    print(f"\n{name} | Shape: {matrix.shape}\n")
    print(df.to_string(float_format=lambda x: f"{x:.2f}"))
