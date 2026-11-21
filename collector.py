
import serial
import time
from pathlib import Path

PORT = "/dev/ttyACM0"
BAUD = 1_000_000

SAMPLES = 16
FRAME_SIZE = 32
TARGET_SIZE = 4 * 1024

OUTPUT = Path("TEST.bin")

ser = serial.Serial(PORT, BAUD, timeout=1)
ser.reset_input_buffer()

total_bytes = 0
valid_frames = 0
invalid_frames = 0
start_time = time.time()

print(f"Target: {TARGET_SIZE} bytes")
print("Receiving...")

try:
    with OUTPUT.open("wb") as file:
        while total_bytes < TARGET_SIZE:
            frame = ser.read(FRAME_SIZE)

            if len(frame) != FRAME_SIZE:
                continue

            values = []
            valid = True

            for i in range(SAMPLES):
                hi = frame[i * 2]
                lo = frame[i * 2 + 1]

                index = hi >> 4
                adc = ((hi & 0x0F) << 8) | lo

                if index != i:
                    valid = False
                    break

                values.append(adc)

            if not valid:
                invalid_frames += 1
                continue

            file.write(frame)
            total_bytes += FRAME_SIZE
            valid_frames += 1

            elapsed = time.time() - start_time
            rate = total_bytes / elapsed / 1024 if elapsed else 0

            print(
                f"\rReceived: {total_bytes}/{TARGET_SIZE} bytes | "
                f"Frames: {valid_frames} | "
                f"Invalid: {invalid_frames} | "
                f"Rate: {rate:.2f} KB/s",
                end="",
                flush=True
            )

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    ser.close()

data = OUTPUT.read_bytes()

samples = [
    ((data[i] & 0x0F) << 8) | data[i + 1]
    for i in range(0, len(data), 2)
]

print("\n\n========== RESULT ==========")
print(f"File:          {OUTPUT}")
print(f"Received:      {len(data)} bytes")
print(f"Valid frames:  {valid_frames}")
print(f"Invalid:       {invalid_frames}")
print(f"Samples:       {len(samples)}")
print(f"ADC min:       {min(samples) if samples else 0}")
print(f"ADC max:       {max(samples) if samples else 0}")
print(f"ADC mean:      {sum(samples) / len(samples) if samples else 0:.3f}")
print(f"Zero samples:  {sum(v == 0 for v in samples)}")
print(f"Non-zero:      {sum(v != 0 for v in samples)}")
print("============================")
