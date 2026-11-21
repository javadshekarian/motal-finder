
from pathlib import Path

FILE = Path("TEST.bin")
SAMPLES = 16
FRAME_SIZE = 32

data = FILE.read_bytes()

print(f"File size: {len(data)} bytes")
print(f"Frames: {len(data) // FRAME_SIZE}\n")

for frame_num in range(len(data) // FRAME_SIZE):
    frame = data[
        frame_num * FRAME_SIZE:
        (frame_num + 1) * FRAME_SIZE
    ]

    values = []

    for i in range(SAMPLES):
        hi = frame[i * 2]
        lo = frame[i * 2 + 1]

        index = hi >> 4
        adc = ((hi & 0x0F) << 8) | lo

        values.append(adc)

    print(
        f"Frame {frame_num:03d}: "
        + " ".join(f"{v:4d}" for v in values)
    )
