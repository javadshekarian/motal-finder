
import struct

FILE = "BASE.bin"
WAVE_COUNT = 1000
SAMPLES_PER_WAVE = 16

with open(FILE, "rb") as f:
    data = f.read()

expected_size = WAVE_COUNT * SAMPLES_PER_WAVE * 2

if len(data) != expected_size:
    raise ValueError(
        f"Invalid file size: {len(data)} bytes, expected {expected_size}"
    )

values = struct.unpack("<16000H", data)

average = []

for sample_index in range(SAMPLES_PER_WAVE):
    total = sum(
        values[wave * SAMPLES_PER_WAVE + sample_index]
        for wave in range(WAVE_COUNT)
    )

    average.append(total / WAVE_COUNT)

print("Average waveform:\n")

for index, value in enumerate(average):
    print(f"Sample {index:02d}: {value:.2f}")

print("\nAverage values:")
print([round(x, 2) for x in average])

with open("AVERAGE.bin", "wb") as f:
    f.write(struct.pack("<16f", *average))

print("\nSaved: AVERAGE.bin")
