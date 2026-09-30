import serial
import numpy as np
import torch
import torch.nn as nn
import subprocess
import math
import struct
import threading
import queue

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

PHASES = 201
MODEL_FILE = "METAL_MODEL.pt"

AI_SAMPLES = 20

SAMPLE_RATE = 44100
BEEP_DURATION = 0.06

BEEP_VOLUME = 0.10
LOUD_BEEP_VOLUME = 0.20

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(1, 16, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(16, 32, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(32, 16, 5, stride=2, padding=2),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(
                16,
                32,
                5,
                stride=2,
                padding=2,
                output_padding=0
            ),
            nn.ReLU(),
            nn.ConvTranspose1d(
                32,
                16,
                5,
                stride=2,
                padding=2,
                output_padding=0
            ),
            nn.ReLU(),
            nn.ConvTranspose1d(
                16,
                1,
                5,
                stride=2,
                padding=2,
                output_padding=0
            )
        )
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        decoded = decoded[:, :, :PHASES]
        if decoded.shape[2] < PHASES:
            decoded = nn.functional.pad(
                decoded,
                (0, PHASES - decoded.shape[2])
            )
        return decoded

checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
    weights_only=False
)

model = ConvAutoencoder().to(DEVICE)
model.load_state_dict(
    checkpoint["model_state"]
)
model.eval()

mean = checkpoint["mean"].astype(
    np.float32
)
scale = float(
    checkpoint["scale"]
)
threshold = float(
    checkpoint["threshold"]
)

if scale < 0.1:
    scale = 0.1

if checkpoint["phases"] != PHASES:
    raise RuntimeError(
        "Model phase count does not match detector"
    )

ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=1
)
ser.reset_input_buffer()

ai_queue = queue.Queue(
    maxsize=AI_SAMPLES
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
        detection = (
            average_score > threshold
        )
        print(
            f"AI average: {average_score:.6f} | "
            f"Threshold: {threshold:.6f} | "
            f"DETECTION: {detection}",
            flush=True
        )
        if detection:
            ratio = (
                average_score /
                threshold
            )
            ratio = max(
                1.0,
                min(ratio, 4.0)
            )
            frequency = int(
                min(
                    2500,
                    500 + ratio * 500
                )
            )
            if ratio > 2.0:
                beep_volume = LOUD_BEEP_VOLUME
            else:
                beep_volume = BEEP_VOLUME
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
            if (
                last_phase == 201
                and phase == 1
            ):
                started = True
                phase_index = 1
                waveform[0] = value
            last_phase = phase
            continue
        expected_phase = (
            phase_index + 1
        )
        if phase != expected_phase:
            if (
                last_phase == 201
                and phase == 1
            ):
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
            normalized = (
                waveform - mean
            ) / scale
            tensor = torch.from_numpy(
                normalized
            ).float().view(
                1,
                1,
                PHASES
            ).to(DEVICE)
            with torch.no_grad():
                reconstructed = model(
                    tensor
                )
                error = torch.mean(
                    (
                        reconstructed -
                        tensor
                    ) ** 2
                ).item()
            print(
                f"Wave: {wave_count} | "
                f"AI: {error:.6f}",
                flush=True
            )
            try:
                ai_queue.put_nowait(
                    error
                )
            except queue.Full:
                pass
            phase_index = 0

ser.close()
