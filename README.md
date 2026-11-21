<h1 align="center">🧲 Arduino Metal Detector — ADC + PCA Waveform Pipeline</h1>

<p align="center">
  <strong>⚡ Arduino UNO · 🎛️ ADC121S021 · 🧲 Coil Driver · 📡 1 Mbit UART · 🧠 PCA Model Builder</strong>
</p>

<p align="center">
  🟢 Firmware &nbsp; 🟦 Collector &nbsp; 🟨 PCA Model &nbsp; 🟪 KiCad Schematic
</p>

---

## ✨ Overview

This project is a **metal-detector / waveform-sampling system** built around:

- 🎛️ An **Arduino UNO R3**
- 🧲 A **MOSFET-driven coil**
- 📈 An external **ADC121S021CISD/NOPB 12-bit ADC**
- 📡 **UART transmission at 1,000,000 baud**
- 🐍 Python host tools for **data collection** and **PCA-based modeling**

The Arduino pulses the coil, samples the returned waveform through SPI, packs the samples into fixed **32-byte frames**, and sends them over UART. On the host side, `collector.py` receives and validates frames, and `model_maker.py` builds a PCA model from waveform data.

> [!NOTE]
> This README is based only on the provided `arduino.c`, `collector.py`, `model_maker.py`, and `CIRCUIT/circuit.kicad_sch`. Other scripts are present in the repository but are not documented here because their contents were not provided.

---

## 🗂️ Repository Layout

```text
.
├── arduino.c
├── av_model_maker.py
├── CIRCUIT
│   ├── circuit.kicad_sch
│   └── circuit.png
├── collector.py
├── debug.py
├── detector.py
├── model_maker.py
├── read_data.py
├── tmp.py
└── wave_builder.py
```

### 📌 Main Files

| File | Role |
|---|---|
| 🟢 `arduino.c` | AVR firmware: coil pulse timing, ADC sampling, frame packing, UART TX |
| 🐍 `collector.py` | Host-side serial collector and frame validator |
| 🧠 `model_maker.py` | PCA model builder for waveform data |
| 🟪 `CIRCUIT/circuit.kicad_sch` | KiCad schematic |
| 🖼️ `CIRCUIT/circuit.png` | Schematic image |

### 🧩 Additional Scripts Present

The repository also contains:

- `av_model_maker.py`
- `debug.py`
- `detector.py`
- `read_data.py`
- `tmp.py`
- `wave_builder.py`

These files are **present in the project tree**, but their behavior is not described here.

---

## 🔌 Hardware Overview

From the KiCad schematic:

| Component | Value / Part | Role |
|---|---|---|
| 🧠 A1 | **Arduino UNO R3** | Main controller |
| 🎛️ U1 | **ADC121S021CISD/NOPB** | External 12-bit ADC with SPI interface |
| ⚡ Q1 | **FQP30N06L** | N-channel MOSFET for coil drive |
| 🧲 L1 | **RX1, 60 turns, Ø0.85 mm wire, wire length ≈ 58 cm** | Sensor / receiver coil |
| 🔋 BT1 | **12 V battery** | Power source for the power stage |
| 🎚️ SW1 | **POWER SWITCH** | Main power switch |
| 🟫 R1 | **100 Ω** | Resistor in the drive/input network |
| 🟫 R2 | **10 kΩ** | Resistor in the drive/input network |
| 🟫 R3 | **100 kΩ** | Resistor in the bias/divider network |
| 🟫 R4 | **10 kΩ** | Resistor in the bias/divider network |
| 🟫 R5 | **10 kΩ** | Resistor in the bias/divider network |
| 🔵 C1 | **100 µF 25 V** | Electrolytic capacitor |
| 🔵 C2 | **470 µF 25 V** | Electrolytic capacitor |
| 🔵 C3 | **100 nF** | Capacitor |
| 🔵 C4 | **100 nF** | Capacitor |
| 🛡️ D1 | **5.1 V Zener** | Protection / clamping |
| 🛡️ D2 | **5.1 V Zener** | Protection / clamping |

---

## 📍 Firmware Pin Map

From `arduino.c`:

| AVR Pin | Arduino Pin | Direction | Function |
|---|---|---|---|
| 🟢 `PB0` | D8 | Output | MOSFET gate drive (`MOSFET_BIT`) |
| 🟡 `PB2` | D10 | Output | ADC chip-select, active low (`ADC_CS_BIT`) |
| 🔵 `PB3` | D11 | SPI | SPI MOSI |
| 🔵 `PB4` | D12 | Input | SPI MISO |
| 🔵 `PB5` | D13 | SPI | SPI SCK |
| 🟣 `PD7` | D7 | Output | Driven low in `setup()` |
| 📡 `PD1` | TX | UART TX | Serial data output |

The SPI interface is configured as **master**.  
The UART is configured for:

- Baud rate: **1,000,000**
- Data format: **8 data bits**
- `UBRR0 = 0` at 16 MHz
- TX enabled

---

## ⚙️ Firmware Behavior — `arduino.c`

### 🧱 Frame Format

```c
#define SAMPLES 16
#define FRAME_SIZE 32
```

- Each frame contains **16 ADC samples**.
- Each sample is packed into **16 bits**:
  - Bits `15..12`: sample index (`0..15`)
  - Bits `11..0`: 12-bit ADC value

| Byte Offset | Content |
|---|---|
| `2*i` | `(index << 4) | (adc >> 8)` |
| `2*i + 1` | `adc & 0xFF` |

This lets the host validate the sample index and recover the ADC value.

---

### ⏱️ Timing

- **Timer1** generates the MOSFET pulse and frame boundary.
  - CTC mode
  - Prescaler: `clk/8`
  - `OCR1A = 779`
  - `OCR1B = 699`
- **Timer2** triggers ADC sampling.
  - CTC mode
  - Prescaler: `clk/8`
  - `OCR2A = 19`
  - Sampling interval: approximately **10 µs**

With a 16 MHz clock and `clk/8` prescaler:

- Timer tick = **0.5 µs**
- Timer1 compare A ≈ **390 µs**
- Timer1 compare B ≈ **350 µs**
- MOSFET high pulse ≈ **40 µs**

The firmware alternates the Timer2 start phase between:

- `TCNT2 = 0`
- `TCNT2 = 10`

It also manually stores the first sample in some phases to align the sampling window.

---

### 🧠 Buffering and Transmission

- Two frame buffers: `wave[2][FRAME_SIZE]`
- Two ready flags: `ready[2]`
- When a frame is complete, its `ready` flag is set.
- UART transmission is started from the Timer1 compare interrupt.
- The UART data-register-empty interrupt (`USART_UDRE_vect`) sends bytes one by one.
- When one frame is finished, the next ready buffer is transmitted if available.

---

## 🐍 Host-Side Data Collection — `collector.py`

### ⚙️ Configuration

```python
PORT = "/dev/ttyACM0"
BAUD = 1_000_000
SAMPLES = 16
FRAME_SIZE = 32
TARGET_SIZE = 4 * 1024
OUTPUT = Path("TEST.bin")
```

### 🔄 Behavior

1. Opens the serial port.
2. Reads exactly `FRAME_SIZE` bytes per frame.
3. Validates each sample index:

   ```python
   index = hi >> 4
   adc = ((hi & 0x0F) << 8) | lo
   ```

   The index must equal the expected sample position.

4. Writes valid frames to `TEST.bin`.
5. Counts valid and invalid frames.
6. Prints progress and final statistics:
   - Received bytes
   - Valid frames
   - Invalid frames
   - Number of samples
   - ADC minimum, maximum, mean
   - Zero and non-zero sample counts

### ▶️ Run

```bash
python3 collector.py
```

Output file:

```text
TEST.bin
```

---

## 🧠 PCA Model Builder — `model_maker.py`

### ⚙️ Configuration

```python
INPUT_FILE = "DATA.bin"
OUTPUT_FILE = "METAL_MODEL.npz"

PHASES = 64
WAVEFORMS = 1005

COMPONENTS = 8

VALIDATION_RATIO = 0.20
THRESHOLD_PERCENTILE = 99.0

EIGENVALUE_FLOOR = 1e-6
```

### 🔄 Behavior

1. Reads `DATA.bin` as little-endian unsigned 16-bit samples (`<u2`).
2. Expects exactly:

   ```text
   WAVEFORMS * PHASES = 1005 * 64 = 64320 samples
   ```

3. Reshapes the data to `(1005, 64)`.
4. Shuffles the waveforms with `np.random.seed(42)`.
5. Splits the data into training and validation sets using `VALIDATION_RATIO`.
6. Computes the mean waveform.
7. Computes the covariance matrix.
8. Computes eigenvalues and eigenvectors.
9. Selects the top `COMPONENTS = 8` principal components.
10. Computes:
    - **Q score** — residual-based score
    - **T² score** — Hotelling’s T²-like score
11. Computes thresholds using the **99th percentile** on the validation set.
12. Saves the model to `METAL_MODEL.npz`.

### 💾 Saved Model Keys

```text
mean
components
eigenvalues
q_threshold
t2_threshold
combined_threshold
phases
components_count
```

### ▶️ Run

```bash
python3 model_maker.py
```

Output file:

```text
METAL_MODEL.npz
```

---

## 🔄 Data Flow

```text
🧲 Coil / MOSFET drive
        │
        ▼
🎛️ ADC121S021 12-bit ADC
        │
        ▼
🧠 Arduino UNO
   ├── Timer1: pulse / frame timing
   ├── Timer2: 16 samples per frame
   └── Packing: index + 12-bit ADC
        │
        ▼
📡 UART @ 1,000,000 baud
        │
        ▼
🐍 collector.py
        │
        ▼
📦 TEST.bin
```

For model training:

```text
🧠 model_maker.py
        │
        ▼
📦 METAL_MODEL.npz
```

> [!WARNING]
> `collector.py` writes `TEST.bin`, while `model_maker.py` reads `DATA.bin` and expects `1005 × 64` samples. Adjust filenames and dimensions before running the model builder on collected data.

---

## 🚀 Quick Start

### 1️⃣ Build and Upload Firmware

Compile and upload `arduino.c` to the Arduino UNO using your AVR/Arduino toolchain.

### 2️⃣ Connect the Serial Port

The collector uses:

```text
/dev/ttyACM0
```

Change `PORT` in `collector.py` if your board appears on a different device.

### 3️⃣ Collect Data

```bash
python3 collector.py
```

This writes valid frames to:

```text
TEST.bin
```

### 4️⃣ Prepare Model Input

`model_maker.py` currently expects:

```text
DATA.bin
1005 waveforms
64 phases per waveform
```

Make sure the input file matches these dimensions and filename, or update the constants in `model_maker.py`.

### 5️⃣ Build the PCA Model

```bash
python3 model_maker.py
```

This produces:

```text
METAL_MODEL.npz
```

---

## ⚠️ Notes and Current Limitations

> [!IMPORTANT]
> - The firmware uses a fixed frame size of **32 bytes** and **16 samples per frame**.
> - Frame validation is based on the **high-nibble sample index**.
> - The ADC value is **12 bits**; the firmware extracts it with `(raw >> 1) & 0x0FFF`.
> - The host collector writes **raw packed frames**, including the index nibble.
> - The PCA model uses **8 principal components**.
> - Thresholds are based on the **99th percentile** of validation scores.
> - The schematic includes a **12 V battery**, power switch, MOSFET, coil, ADC, protection Zeners, resistors, and capacitors.
> - Additional scripts (`av_model_maker.py`, `debug.py`, `detector.py`, `read_data.py`, `tmp.py`, `wave_builder.py`) are present but are not documented here.

---

## ✅ Summary

| Part | Status |
|---|---|
| 🧲 Coil + MOSFET drive | ✅ In firmware & schematic |
| 🎛️ ADC121S021 sampling | ✅ In firmware & schematic |
| 📦 16-sample / 32-byte frames | ✅ In firmware |
| 📡 1 Mbit UART transmission | ✅ In firmware & collector |
| 🐍 Frame validation | ✅ In `collector.py` |
| 🧠 PCA model builder | ✅ In `model_maker.py` |
| 🟪 KiCad schematic | ✅ In `CIRCUIT/` |
| 🧩 Extra scripts | 📁 Present, not documented |

<p align="center">
  🧲 ⚡ 🎛️ 📡 🐍 🧠 🟪
</p>
