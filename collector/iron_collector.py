import serial
import numpy as np
import time

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

PHASES = 201
WAVEFORMS = 1000

OUTPUT_FILE = "../results/IRON_DATA.bin"

SYNC_PHASES = 8

ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=None
)

ser.reset_input_buffer()

buffer = bytearray()

waveform = np.empty(
    PHASES,
    dtype=np.uint16
)

synced = False
phase_index = 0
waveform_count = 0

last_log = time.time()
total_bytes = 0

with open(OUTPUT_FILE, "wb") as f:

    while waveform_count < WAVEFORMS:

        data = ser.read(4096)

        if not data:
            continue

        buffer.extend(data)
        total_bytes += len(data)

        if not synced:

            found = False

            max_offset = min(
                3,
                len(buffer)
            )

            for offset in range(max_offset):

                required = offset + (SYNC_PHASES * 3)

                if len(buffer) < required:
                    break

                valid = True

                for i in range(SYNC_PHASES):

                    phase = buffer[
                        offset + i * 3 + 2
                    ]

                    if phase != i + 1:
                        valid = False
                        break

                if valid:

                    if offset:
                        del buffer[:offset]

                    synced = True
                    phase_index = 0
                    found = True

                    break

            if not found:

                if len(buffer) > 32:
                    del buffer[:-32]

                if time.time() - last_log >= 2:

                    print(
                        f"Waiting for sync | "
                        f"received: {total_bytes} bytes",
                        flush=True
                    )

                    last_log = time.time()

                continue

        while synced and len(buffer) >= 3:

            value = (
                buffer[0]
                | (buffer[1] << 8)
            )

            phase = buffer[2]

            del buffer[:3]

            expected_phase = phase_index + 1

            if phase != expected_phase:

                synced = False
                phase_index = 0

                break

            waveform[phase_index] = value

            phase_index += 1

            if phase_index == PHASES:

                waveform.tofile(f)
                f.flush()

                waveform_count += 1

                samples = (
                    waveform_count * PHASES
                )

                size = (
                    waveform_count
                    * PHASES
                    * 2
                )

                print(
                    f"{waveform_count}/{WAVEFORMS} waves | "
                    f"{samples} samples | "
                    f"{size} bytes",
                    flush=True
                )

                synced = False
                phase_index = 0

ser.close()

print()
print("COLLECTION COMPLETE")
print(f"Waveforms: {waveform_count}")
print(f"Samples:   {waveform_count * PHASES}")
print(f"Bytes:     {waveform_count * PHASES * 2}")
print(f"Output:    {OUTPUT_FILE}")
