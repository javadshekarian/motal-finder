# Arduino PI Metal Detector – Waveform Acquisition

---

## Overview

This project uses an Arduino-based Pulse Induction (PI) metal detector to acquire, analyze, and model electromagnetic response waveforms.

The system captures **16 ADC samples per waveform** and uses a **13-position repeating cycle** to characterize the baseline signal. The collected data is used to build statistical matrices that represent the detector's normal behavior in the absence of metal.

A Linux serial proxy is used between the Arduino and the Python collector to improve data acquisition stability and provide a virtual serial interface.

---

## System Architecture

```text
┌─────────────────────┐
│     Arduino Uno     │
│                     │
│ PI Pulse Generation │
│ ADC Sampling        │
│ 16 Samples/Wave     │
│ 13-Position Cycle   │
└──────────┬──────────┘
           │ USB Serial
           ▼
┌─────────────────────┐
│    serial_proxy     │
│                     │
│ Serial Forwarding   │
│ Virtual Serial Port │
│ Counter Handling    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Python Collector   │
│                     │
│ Waveform Capture    │
│ Data Validation     │
│ Binary Storage      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  build_matrices.py  │
│                     │
│ Baseline Modeling   │
│ Statistical Analysis│
└─────────────────────┘
```

---

## Requirements

### Hardware

| | |
|---|---|
| Arduino Uno | PI detection coil |
| MOSFET switching circuit | ADC sampling circuit |
| USB connection to a Linux computer | |

### Software

| | |
|---|---|
| Linux | Arduino firmware |
| Python 3 | `pyserial` |
| GCC/G++ compiler | |

Install the Python serial dependency if needed:

```bash
pip install pyserial
```

---

## Important: Serial Proxy

> [!IMPORTANT]
> **The collector must communicate with the Arduino through `serial_proxy`, not directly through `/dev/ttyACM0`.**

The serial proxy performs the forwarding between the physical Arduino serial interface and a virtual serial port. The Python collector connects to this virtual port.

This setup provides a stable acquisition workflow and supports the 13-position waveform cycle used by the baseline model.

The communication flow is:

```text
Arduino: /dev/ttyACM0
          │
          ▼
     serial_proxy
          │
          ▼
Virtual Port: /tmp/arduino-proxy
          │
          ▼
      collector.py
```

---

## Installation and Setup

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Make sure the Arduino firmware is uploaded to the Arduino Uno.

The Arduino should be connected and available at:

```text
/dev/ttyACM0
```

---

## Step 1 – Compile the Serial Proxy

Navigate to the project directory:

```bash
cd arduino
```

Compile `serial_proxy.cpp`:

```bash
g++ -std=c++17 -Wall -Wextra -O2 serial_proxy.cpp -o serial_proxy -lutil
```

This generates the `serial_proxy` executable.

---

## Step 2 – Start the Serial Proxy

Run:

```bash
./serial_proxy
```

The proxy will initialize the Arduino connection and create a virtual serial port.

Example output:

```text
Waiting 2 seconds for Arduino startup...
Arduino input : /dev/ttyACM0
Python port   : /tmp/arduino-proxy -> /dev/pts/3
Counter       : enabled (0..12)
Press Ctrl+C to stop.
```

Keep this terminal open while collecting data.

> [!WARNING]
> **Do not close the proxy while the collector is running.**

---

## Step 3 – Configure the Collector

Open `collector.py` and make sure the serial port is set to the virtual port:

```python
PORT = "/tmp/arduino-proxy"
BAUD = 1000000
```

The collector must not use `/dev/ttyACM0` directly.

---

## Step 4 – Collect Baseline Data

Open a second terminal in the project directory.

Run the collector:

```bash
python3 collector.py
```

The collector captures waveform data and stores it in the binary data file.

For baseline acquisition, make sure:

- [ ] No metal object is near the detection coil.
- [ ] The coil remains stationary.
- [ ] The electrical environment remains unchanged during acquisition.
- [ ] The serial proxy is running.
- [ ] The collector is connected to `/tmp/arduino-proxy`.

The collected baseline data is saved as:

```text
BASE.bin
```

---

## Step 5 – Build the Baseline Matrices

After collecting the baseline data, run:

```bash
python3 build_matrices.py
```

The script analyzes the collected waveforms and generates three statistical matrices.

### BASE_MEAN

The mean ADC value for each sample position across the 13-position cycle.

Shape:

```text
(13, 16)
```

Each row represents one position in the repeating cycle, and each column represents one of the 16 ADC sample points.

### MAX_NOISE

The maximum positive deviation from the mean for each position and sample.

### MIN_NOISE

The maximum negative deviation from the mean for each position and sample.

These matrices characterize the baseline response and its natural variation.

---

## Data Structure

Each waveform contains **16 ADC samples**.

The system uses a repeating cycle of **13 positions**:

```text
Position 1
Position 2
Position 3
...
Position 13
Position 1
Position 2
...
```

The baseline model therefore contains:

```text
13 Positions × 16 Samples
```

The resulting matrices preserve the differences between the 13 waveform positions rather than treating every waveform as identical.

---

## Typical Workflow

For a complete baseline acquisition:

```text
1. Connect the Arduino.
2. Upload the Arduino firmware.
3. Compile serial_proxy.cpp.
4. Start serial_proxy.
5. Open a second terminal.
6. Run collector.py.
7. Capture baseline data into BASE.bin.
8. Run build_matrices.py.
9. Inspect BASE_MEAN, MAX_NOISE and MIN_NOISE.
```

---

## Troubleshooting

### Arduino serial port is unavailable

Check connected serial devices:

```bash
ls /dev/ttyACM*
```

Make sure the Arduino is connected and that the configured port in `serial_proxy.cpp` matches the device.

### Permission denied on the serial port

Check the current user's permissions:

```bash
groups
```

If necessary, add the user to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
```

Log out and log back in for the group change to take effect.

### Collector cannot open the serial port

Verify that `serial_proxy` is running and that the collector is configured to use:

```text
/tmp/arduino-proxy
```

Do not run the collector directly against `/dev/ttyACM0` while using the proxy workflow.

### Proxy stops working

Stop the collector first, restart `serial_proxy`, and then restart the collector.

---

## Notes

> [!NOTE]
> - Keep the acquisition hardware and coil configuration unchanged when collecting baseline data.
> - Avoid moving the coil during baseline acquisition.
> - Electrical interference can affect ADC measurements and baseline statistics.
> - Use the serial proxy for waveform collection.
> - The baseline model is based on the 13-position cycle and 16 samples per waveform.

---
