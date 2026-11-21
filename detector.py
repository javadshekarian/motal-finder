import serial
import numpy as np
import subprocess
import math
import struct
import threading
import queue

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

PHASES = 64

MODEL_FILE = "METAL_MODEL.npz"

AI_SAMPLES = 3

SAMPLE_RATE = 44100
BEEP_DURATION = 0.06

BEEP_VOLUME = 0.10
LOUD_BEEP_VOLUME = 0.20


model = np.load(
    MODEL_FILE
)

mean = model["mean"].astype(
    np.float32
)

components = model[
    "components"
].astype(
    np.float32
)

eigenvalues = model[
    "eigenvalues"
].astype(
    np.float32
)

q_threshold = float(
    model["q_threshold"]
)

t2_threshold = float(
    model["t2_threshold"]
)

combined_threshold = float(
    model["combined_threshold"]
)

model_phases = int(
    model["phases"]
)

components_count = int(
    model["components_count"]
)

if model_phases != PHASES:

    raise RuntimeError(
        "Model phase count does not match detector"
    )

if components.shape != (
    PHASES,
    components_count
):

    raise RuntimeError(
        "Invalid PCA component shape"
    )

if len(eigenvalues) != components_count:

    raise RuntimeError(
        "Invalid PCA eigenvalue count"
    )

print(
    f"Q threshold: {q_threshold:.6f}"
)

print(
    f"T2 threshold: {t2_threshold:.6f}"
)

print(
    f"Combined threshold: "
    f"{combined_threshold:.6f}"
)

print(
    f"Components: {components_count}"
)

print()


ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=1
)

ser.reset_input_buffer()

ai_queue = queue.Queue(
    maxsize=AI_SAMPLES
)


def calculate_scores(
    waveform
):

    centered = (
        waveform -
        mean
    )

    latent = (
        centered @
        components
    )

    reconstructed = (
        latent @
        components.T
    )

    residual = (
        centered -
        reconstructed
    )

    q_score = float(
        np.sum(
            residual *
            residual
        )
    )

    t2_score = float(
        np.sum(
            (
                latent *
                latent
            ) /
            np.maximum(
                eigenvalues,
                1e-6
            )
        )
    )

    q_ratio = (
        q_score /
        max(
            q_threshold,
            1e-12
        )
    )

    t2_ratio = (
        t2_score /
        max(
            t2_threshold,
            1e-12
        )
    )

    combined_score = max(
        q_ratio,
        t2_ratio
    )

    return (
        q_score,
        t2_score,
        combined_score
    )


def beep_worker():

    scores = []

    while True:

        score = ai_queue.get()

        scores.append(score)

        if len(scores) < AI_SAMPLES:

            ai_queue.task_done()

            continue

        average_score = float(
            np.mean(scores)
        )

        peak_score = float(
            np.max(scores)
        )

        detection = (
            peak_score >
            combined_threshold
        )

        print(
            f"Score: {average_score:.6f} | "
            f"Peak: {peak_score:.6f} | "
            f"Threshold: {combined_threshold:.6f} | "
            f"DETECTION: {detection}",
            flush=True
        )

        if detection:

            ratio = max(
                1.0,
                min(
                    peak_score /
                    max(
                        combined_threshold,
                        1e-12
                    ),
                    4.0
                )
            )

            frequency = int(
                min(
                    2500,
                    500 +
                    ratio * 500
                )
            )

            if ratio > 2.0:

                beep_volume = (
                    LOUD_BEEP_VOLUME
                )

            else:

                beep_volume = (
                    BEEP_VOLUME
                )

            samples = int(
                SAMPLE_RATE *
                BEEP_DURATION
            )

            fade_samples = int(
                SAMPLE_RATE *
                0.004
            )

            audio = bytearray()

            for i in range(samples):

                if i < fade_samples:

                    envelope = (
                        i /
                        fade_samples
                    )

                elif (
                    i >=
                    samples -
                    fade_samples
                ):

                    envelope = (
                        samples -
                        i
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

        scores.clear()

        ai_queue.task_done()


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

synced = False
phase_index = 0
wave_count = 0


def find_sync():

    global buffer

    required = 16

    if len(buffer) < required:

        return False

    max_offset = (
        len(buffer) -
        required +
        1
    )

    for offset in range(
        max_offset
    ):

        valid = True

        for i in range(8):

            packet = (
                buffer[
                    offset +
                    i * 2
                ]
                |
                (
                    buffer[
                        offset +
                        i * 2 +
                        1
                    ]
                    << 8
                )
            )

            phase = (
                packet >> 10
            ) & 0x3F

            if phase != i:

                valid = False

                break

        if valid:

            if offset:

                del buffer[
                    :offset
                ]

            return True

    if len(buffer) > 1:

        del buffer[:-1]

    return False


while True:

    data = ser.read(4096)

    if not data:

        continue

    buffer.extend(data)

    if not synced:

        synced = find_sync()

        if not synced:

            continue

        phase_index = 0

    while synced and len(buffer) >= 2:

        packet = (
            buffer[0]
            |
            (
                buffer[1]
                << 8
            )
        )

        value = (
            packet &
            0x03FF
        )

        phase = (
            packet >> 10
        ) & 0x3F

        del buffer[:2]

        if phase_index < PHASES:

            expected_phase = (
                phase_index
            )

            if phase != expected_phase:

                synced = False
                phase_index = 0

                break

            waveform[
                phase_index
            ] = value

            phase_index += 1

        else:

            if phase != 0:

                synced = False
                phase_index = 0

                break

            q_score, t2_score, combined_score = (
                calculate_scores(
                    waveform
                )
            )

            wave_count += 1

            print(
                f"Wave: {wave_count} | "
                f"Q: {q_score:.6f} | "
                f"T2: {t2_score:.6f} | "
                f"Score: {combined_score:.6f}",
                flush=True
            )

            try:

                ai_queue.put_nowait(
                    combined_score
                )

            except queue.Full:

                pass

            waveform[0] = value

            phase_index = 1


ser.close()