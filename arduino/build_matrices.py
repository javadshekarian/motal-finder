
import numpy as np
import pandas as pd
from pathlib import Path

data = np.fromfile("BASE.bin", dtype="<u2").reshape(-1, 16)

GROUP_SIZE = 13
group_count = len(data) // GROUP_SIZE

groups = data[:group_count * GROUP_SIZE].reshape(group_count, GROUP_SIZE, 16)

output_dir = Path("matrices")
output_dir.mkdir(exist_ok=True)

for sample in range(16):
    matrix = groups[:, :, sample]

    df = pd.DataFrame(
        matrix,
        index=[f"Group {i+1}" for i in range(group_count)],
        columns=[f"Position {i+1}" for i in range(GROUP_SIZE)]
    )

    print(f"\nSample {sample+1} | Shape: {df.shape}")
    print(df.to_string())
