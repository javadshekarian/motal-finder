import os
import numpy as np
import matplotlib.pyplot as plt

PHASES = 201

DATA_FILE = "DATA.bin"
IRON_FILE = "IRON_DATA.bin"

OUTPUT_DIR = "analysis"
OUTPUT_FILE = "average_base_vs_iron.png"


def load_waveforms(filename):
    with open(filename, "rb") as f:
        data = f.read()

    if len(data) % 2 != 0:
        raise RuntimeError(
            f"{filename}: file size is not divisible by 2"
        )

    raw = np.frombuffer(
        data,
        dtype="<u2"
    )

    waveform_count = len(raw) // PHASES

    if waveform_count == 0:
        raise RuntimeError(
            f"{filename}: no complete waveforms found"
        )

    raw = raw[
        :waveform_count * PHASES
    ]

    return raw.reshape(
        waveform_count,
        PHASES
    ).astype(np.float64)


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    print("Loading waveforms...")

    base = load_waveforms(
        DATA_FILE
    )

    iron = load_waveforms(
        IRON_FILE
    )

    print(
        f"BASE waveforms: {len(base)}"
    )

    print(
        f"IRON waveforms: {len(iron)}"
    )

    base_average = np.mean(
        base,
        axis=0
    )

    iron_average = np.mean(
        iron,
        axis=0
    )

    phases = np.arange(
        1,
        PHASES + 1
    )

    plt.figure(
        figsize=(15, 8)
    )

    plt.plot(
        phases,
        base_average,
        linewidth=2.5,
        label="BASE"
    )

    plt.plot(
        phases,
        iron_average,
        linewidth=2.5,
        label="IRON"
    )

    plt.xlabel(
        "Phase"
    )

    plt.ylabel(
        "ADC"
    )

    plt.title(
        "Average Waveform: BASE vs IRON"
    )

    plt.xlim(
        1,
        PHASES
    )

    plt.grid(
        True,
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    output_path = os.path.join(
        OUTPUT_DIR,
        OUTPUT_FILE
    )

    plt.savefig(
        output_path,
        dpi=300
    )

    plt.close()

    difference = (
        iron_average - base_average
    )

    max_phase = np.argmax(
        np.abs(difference)
    )

    print()
    print(
        f"Maximum difference phase: "
        f"{max_phase + 1}"
    )

    print(
        f"BASE ADC: "
        f"{base_average[max_phase]:.6f}"
    )

    print(
        f"IRON ADC: "
        f"{iron_average[max_phase]:.6f}"
    )

    print(
        f"Difference: "
        f"{difference[max_phase]:.6f}"
    )

    print()
    print(
        f"Saved: {output_path}"
    )


if __name__ == "__main__":
    main()
