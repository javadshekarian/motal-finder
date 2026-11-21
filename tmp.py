import numpy as np

data = np.fromfile("BASE_MODEL.bin", dtype="<u2")

if len(data) % 64 != 0:
    raise ValueError(f"Invalid file size: {len(data)} samples")

waves = data.reshape(-1, 64)

print(f"Total samples: {len(data)}")
print(f"Total waveforms: {len(waves)}")

for i, wave in enumerate(waves[:3], 1):
    print(f"\nWaveform {i}:")
    print(wave.tolist())
    print(f"Min: {wave.min()} | Max: {wave.max()} | Mean: {wave.mean():.2f}")