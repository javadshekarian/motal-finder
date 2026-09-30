import serial
import numpy as np
import subprocess
import math
import struct
import threading
import queue

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

PHASES = 201
BASE_FILE = "BASE_MODEL.npz"

MAX_SAMPLES = 20

BEEP_THRESHOLD = 9
LOUD_BEEP_THRESHOLD = 13

BEEP_DURATION = 0.06
SAMPLE_RATE = 44100

BEEP_VOLUME = 0.10
LOUD_BEEP_VOLUME = 0.20

ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=1
)

ser.reset_input_buffer()

model = np.load(BASE_FILE)

base_waveform = model["base_waveform"].astype(np.float32)

if base_waveform.shape != (PHASES,):
    raise RuntimeError(
        f"Invalid base waveform shape: {base_waveform.shape}"
    )

max_queue = queue.Queue(maxsize=MAX_SAMPLES)


def beep_worker():

    max_values = []

    while True:

        max_difference = max_queue.get()

        max_values.append(max_difference)

        if len(max_values) < MAX_SAMPLES:

            max_queue.task_done()
            continue

        average_max = np.mean(max_values)

        if average_max > BEEP_THRESHOLD:

            if average_max > LOUD_BEEP_THRESHOLD:

                beep_volume = LOUD_BEEP_VOLUME

            else:

                beep_volume = BEEP_VOLUME

            frequency = int(
                min(
                    2500,
                    500 + average_max * 100
                )
            )

            samples = int(
                SAMPLE_RATE * BEEP_DURATION
            )

            fade_samples = int(
                SAMPLE_RATE * 0.004
            )

            audio = bytearray()

            for i in range(samples):

                if i < fade_samples:

                    envelope = i / fade_samples

                elif i >= samples - fade_samples:

                    envelope = (
                        samples - i
                    ) / fade_samples

                else:

                    envelope = 1.0

                value = int(
                    32767
                    * beep_volume
                    * envelope
                    * math.sin(
                        2
                        * math.pi
                        * frequency
                        * i
                        / SAMPLE_RATE
                    )
                )

                audio.extend(
                    struct.pack(
                        "<h",
                        value
                    )
                )

            process = subprocess.Popen(
                [
                    "aplay",
                    "-q",
                    "-f",
                    "S16_LE",
                    "-r",
                    str(SAMPLE_RATE),
                    "-c",
                    "1"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            try:

                process.communicate(
                    bytes(audio)
                )

            except Exception:

                process.kill()

        max_values.clear()

        max_queue.task_done()


audio_thread = threading.Thread(
    target=beep_worker,
    daemon=True
)

audio_thread.start()


buffer = bytearray()

waveform = np.empty(
    PHASES,
    dtype=np.float32
)

phase_index = 0
wave_count = 0

started = False
last_phase = None


while True:

    data = ser.read(4096)

    if not data:
        continue

    buffer.extend(data)

    while len(buffer) >= 3:

        value = (
            buffer[0]
            | (buffer[1] << 8)
        )

        phase = buffer[2]

        del buffer[:3]

        if not started:

            if last_phase == 201 and phase == 1:

                started = True
                phase_index = 1
                waveform[0] = value

            last_phase = phase
            continue

        expected_phase = phase_index + 1

        if phase != expected_phase:

            if last_phase == 201 and phase == 1:

                phase_index = 1
                waveform[0] = value

            else:

                started = False
                phase_index = 0

            last_phase = phase
            continue

        waveform[phase_index] = value

        phase_index += 1
        last_phase = phase

        if phase_index == PHASES:

            wave_count += 1

            difference = (
                waveform - base_waveform
            )

            abs_difference = np.abs(
                difference
            )

            rmse = np.sqrt(
                np.mean(
                    difference * difference
                )
            )

            max_difference = np.max(
                abs_difference
            )

            print(
                f"Wave: {wave_count} | "
                f"RMSE: {rmse:.2f} | "
                f"MAX: {max_difference:.2f}",
                flush=True
            )

            try:

                max_queue.put_nowait(
                    max_difference
                )

            except queue.Full:

                pass

            phase_index = 0


ser.close()
