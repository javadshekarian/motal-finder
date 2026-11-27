import numpy as np
import pandas as pd

FILE = "BASE.bin"
SAMPLES_PER_WAVE = 16
WAVE_COUNT = 13

raw = np.fromfile(FILE, dtype="<u2")

if len(raw) % SAMPLES_PER_WAVE != 0:
    raise ValueError("Invalid BASE.bin size")

data = raw.reshape(-1, SAMPLES_PER_WAVE)

waves = [[] for _ in range(WAVE_COUNT)]

for wave in data:
    for sample_index, value in enumerate(wave):
        if (value >> 12) != sample_index:
            raise ValueError("Invalid sample index")

    counter_low = (wave[1] >> 10) & 0b11
    counter_high = (wave[2] >> 10) & 0b11

    phase = (counter_high << 2) | counter_low

    if phase >= WAVE_COUNT:
        raise ValueError(f"Invalid phase: {phase}")

    adc_values = wave & 0x03FF

    waves[phase].append(adc_values)

counts = np.array([len(wave) for wave in waves])

if np.any(counts == 0):
    raise ValueError("Some phases have no data")

groups = np.array([
    np.array(wave_data)
    for wave_data in waves
], dtype=object)

BASE_MEAN = np.zeros((WAVE_COUNT, SAMPLES_PER_WAVE))
MAX_NOISE = np.zeros((WAVE_COUNT, SAMPLES_PER_WAVE))
MIN_NOISE = np.zeros((WAVE_COUNT, SAMPLES_PER_WAVE))

for phase in range(WAVE_COUNT):
    phase_data = np.array(waves[phase])

    BASE_MEAN[phase] = np.mean(phase_data, axis=0)

    differences = phase_data - BASE_MEAN[phase]

    MAX_NOISE[phase] = np.max(differences, axis=0)
    MIN_NOISE[phase] = np.min(differences, axis=0)

matrices = {
    "BASE_MEAN": BASE_MEAN,
    "MAX_NOISE": MAX_NOISE,
    "MIN_NOISE": MIN_NOISE
}

for name, matrix in matrices.items():
    df = pd.DataFrame(
        matrix,
        index=[f"Wave {i+1}" for i in range(WAVE_COUNT)],
        columns=[f"Sample {i+1}" for i in range(SAMPLES_PER_WAVE)]
    )

    print(f"\n{name} | Shape: {matrix.shape}\n")
    print(df.to_string(float_format=lambda x: f"{x:.2f}"))

print("\n==============================")
print("Wave counts")
print("==============================")

for i, count in enumerate(counts):
    print(f"Wave {i+1:02d}: {count} samples")