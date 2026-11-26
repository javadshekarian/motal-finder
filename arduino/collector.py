import serial
import struct
import time

PORT = "/tmp/arduino-proxy"
BAUD = 1000000

CAPTURE_SECONDS = 4.0
WAVE_COUNT = 1000
SAMPLES_PER_WAVE = 16
FRAME_SIZE = 32

def decode_frame(data):
    words = struct.unpack("<16H", data)

    for index, word in enumerate(words):
        if (word >> 12) != index:
            return None
        if index not in (1, 2) and (word & 0x0C00):
            return None

    return [word & 0x03FF for word in words]

def main():
    raw = bytearray()

    print(f"Port: {PORT}")
    print(f"Capturing for {CAPTURE_SECONDS} seconds...", flush=True)

    with serial.Serial(PORT, BAUD, timeout=0.05) as ser:
        time.sleep(2)
        ser.reset_input_buffer()

        start = time.monotonic()
        last_report = start

        while time.monotonic() - start < CAPTURE_SECONDS:
            chunk = ser.read(max(1, ser.in_waiting))

            if chunk:
                raw.extend(chunk)

            now = time.monotonic()

            if now - last_report >= 1:
                print(f"Received: {len(raw)} bytes", flush=True)
                last_report = now

    print(f"\nTotal received: {len(raw)} bytes")
    print("Searching for wave alignment...", flush=True)

    best_offset = None
    best_count = 0

    for offset in range(FRAME_SIZE):
        count = 0
        pos = offset

        while pos + FRAME_SIZE <= len(raw):
            if decode_frame(raw[pos:pos + FRAME_SIZE]) is not None:
                count += 1
            pos += FRAME_SIZE

        if count > best_count:
            best_count = count
            best_offset = offset

    if best_offset is None or best_count == 0:
        print("No valid waves found!")
        return

    print(f"Alignment offset: {best_offset}")
    print(f"Valid waves found: {best_count}")

    waves = []

    pos = best_offset

    while pos + FRAME_SIZE <= len(raw) and len(waves) < WAVE_COUNT:
        values = decode_frame(raw[pos:pos + FRAME_SIZE])

        if values is not None:
            waves.append(values)

        pos += FRAME_SIZE

    if len(waves) != WAVE_COUNT:
        print(f"Not enough waves: {len(waves)}/{WAVE_COUNT}")
        return

    with open("BASE.bin", "wb") as file:
        for wave in waves:
            file.write(struct.pack("<16H", *wave))

    print("\nCollection completed.")
    print(f"Waves: {len(waves)}")
    print(f"Samples: {len(waves) * SAMPLES_PER_WAVE}")
    print(f"File size: {len(waves) * FRAME_SIZE} bytes")
    print("Saved: BASE.bin")

if __name__ == "__main__":
    main()