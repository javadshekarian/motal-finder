import numpy as np

INPUT_FILE = "DATA.bin"
OUTPUT_FILE = "BASE_MODEL.npz"

PHASES = 201

data = np.fromfile(
    INPUT_FILE,
    dtype="<u2"
)

wave_count = len(data) // PHASES

if wave_count == 0:
    raise RuntimeError("No complete waveform found")

data = data[:wave_count * PHASES]

waves = data.reshape(
    wave_count,
    PHASES
)

base_waveform = np.mean(
    waves,
    axis=0
)

np.savez(
    OUTPUT_FILE,
    base_waveform=base_waveform.astype(np.float32),
    phases=np.arange(
        1,
        PHASES + 1,
        dtype=np.uint8
    ),
    waveform_count=wave_count
)

print("BASE MODEL CREATED")
print("-------------------")
print(f"Samples:    {len(data)}")
print(f"Waveforms:  {wave_count}")
print(f"Phases:     {PHASES}")
print(f"Output:     {OUTPUT_FILE}")
