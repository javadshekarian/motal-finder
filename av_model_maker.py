
import numpy as np

INPUT = "BASE.bin"
SAMPLES = 16
FRAME_SIZE = 32

data = np.fromfile(INPUT, dtype=np.uint8)

if len(data) % FRAME_SIZE:
    raise ValueError("Invalid file size")

frames = data.reshape(-1, SAMPLES, 2)

indices = frames[:, :, 0] >> 4

if not np.all(indices == np.arange(SAMPLES)):
    raise ValueError("Invalid sample indices")

adc = (
    ((frames[:, :, 0] & 0x0F).astype(np.uint16) << 8)
    | frames[:, :, 1].astype(np.uint16)
)

mean = np.mean(adc, axis=0)

np.save("BASE_MEAN.npy", mean)

print(f"Waves: {len(frames)}")
print(f"Total samples: {adc.size}")
print("\nMean ADC values:\n")

for i, value in enumerate(mean):
    print(f"Sample {i:02d}: {value:.4f}")

print("\nSaved: BASE_MEAN.npy")
