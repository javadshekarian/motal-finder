
import numpy as np
import pandas as pd

GROUP_SIZE = 13
OFFSET = 12

# Load BASE
base_data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16)

base_groups = base_data[:988].reshape(76, 13, 16)

BASE_MEAN = np.mean(base_groups, axis=0)
BASE_MAX_NOISE = np.max(base_groups - BASE_MEAN, axis=0)
BASE_MIN_NOISE = np.min(base_groups - BASE_MEAN, axis=0)

# Load METAL
metal_data = np.fromfile("METAL.bin", dtype="<u2").reshape(-1, 16)

# Align METAL using offset 12
metal_aligned = metal_data[OFFSET:OFFSET + 988]

metal_groups = metal_aligned.reshape(76, 13, 16)

METAL_MEAN = np.mean(metal_groups, axis=0)

# Calculate differences
DIFFERENCE = METAL_MEAN - BASE_MEAN

# Calculate baseline noise boundaries
LOWER_LIMIT = BASE_MEAN + BASE_MIN_NOISE
UPPER_LIMIT = BASE_MEAN + BASE_MAX_NOISE

# Detect values outside baseline noise
OUTSIDE = (
    (METAL_MEAN < LOWER_LIMIT) |
    (METAL_MEAN > UPPER_LIMIT)
)

# Display matrices
matrices = {
    "METAL_MEAN": METAL_MEAN,
    "DIFFERENCE": DIFFERENCE,
    "OUTSIDE_NOISE": OUTSIDE.astype(int)
}

for name, matrix in matrices.items():
    df = pd.DataFrame(
        matrix,
        index=[f"Position {i+1}" for i in range(13)],
        columns=[f"Sample {i+1}" for i in range(16)]
    )

    print(f"\n{name} | Shape: {matrix.shape}\n")
    print(df.to_string(float_format=lambda x: f"{x:.2f}"))

print("\nTotal cells outside baseline noise:", np.count_nonzero(OUTSIDE))
print("Total cells:", OUTSIDE.size)
print("Outside percentage:", np.mean(OUTSIDE) * 100, "%")
