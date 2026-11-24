
import struct

FILE = "BASE.bin"
WAVE_COUNT = 80
SAMPLES_PER_WAVE = 16

with open(FILE, "rb") as f:
    data = f.read()

values = struct.unpack(
    f"<{len(data) // 2}H",
    data
)

for wave in range(WAVE_COUNT):
    start = wave * SAMPLES_PER_WAVE
    samples = values[start:start + SAMPLES_PER_WAVE]

    print(f"Wave {wave + 1:03d}: {list(samples)}")
