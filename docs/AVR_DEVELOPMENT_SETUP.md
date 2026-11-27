# ⚡ AVR Development Environment
### Arduino Uno · ATmega328P · Ubuntu Linux

> **Development environment reference**  
> A reproducible setup for AVR firmware development, Arduino Core headers, toolchain configuration, and VS Code IntelliSense.

---

## 01 — Environment Overview

| Component | Configuration |
|---|---|
| Host OS | Ubuntu Linux |
| Board | Arduino Uno |
| MCU | ATmega328P |
| Architecture | AVR 8-bit |
| Clock Frequency | 16 MHz |
| Compiler | AVR-GCC / AVR-G++ |
| C Standard | GNU C11 |
| C++ Standard | GNU C++17 |
| Arduino Core | Arduino AVR Core |
| IDE / Editor | Visual Studio Code |
| IntelliSense | Microsoft C/C++ Extension |

The firmware is developed for the **ATmega328P**, the 8-bit microcontroller used on the Arduino Uno.

The development environment requires the AVR toolchain, AVR libc, Arduino AVR Core, and the appropriate include paths for the microcontroller and board variant.

---

## 02 — Required Packages

Install the required packages using APT:

```bash
sudo apt update

sudo apt install -y \
    build-essential \
    gcc-avr \
    avr-libc \
    arduino-core-avr
```

### Package responsibilities

| Package | Purpose |
|---|---|
| `build-essential` | Host-side development tools, including GCC, G++, Make and related utilities |
| `gcc-avr` | AVR cross-compiler, including `avr-gcc` and `avr-g++` |
| `avr-libc` | AVR standard C library, device definitions, interrupt support and low-level headers |
| `arduino-core-avr` | Arduino AVR Core, including `Arduino.h`, core implementation and board variants |

> **Note:** The Arduino IDE is not required for this toolchain configuration. The compiler, device libraries, and Arduino Core can be installed and used independently.

---

## 03 — AVR Compiler Toolchain

### Required compiler

The firmware must use the AVR cross-compiler:

```text
/usr/bin/avr-g++
```

The corresponding C compiler is:

```text
/usr/bin/avr-gcc
```

Verify the installation:

```bash
avr-g++ --version
avr-gcc --version
```

Check that the compiler is available:

```bash
which avr-g++
```

Expected location:

```text
/usr/bin/avr-g++
```

### Target microcontroller

The compiler target must be set to:

```text
-mmmcu=atmega328p
```

The correct compiler argument is:

```bash
-mmcu=atmega328p
```

This specifies the target architecture and allows the compiler to use the appropriate MCU definitions, instruction set, registers, and device-specific features.

---

## 04 — Arduino AVR Core

The Arduino Core provides the Arduino platform headers and implementation.

### Arduino Core location

```text
/usr/share/arduino/hardware/arduino/avr/cores/arduino
```

The main Arduino header is located at:

```text
/usr/share/arduino/hardware/arduino/avr/cores/arduino/Arduino.h
```

### Arduino Uno variant

```text
/usr/share/arduino/hardware/arduino/avr/variants/standard
```

This directory contains board-specific definitions, including pin mappings and related configuration headers.

### Required include paths

```text
/usr/share/arduino/hardware/arduino/avr/cores/arduino
/usr/share/arduino/hardware/arduino/avr/variants/standard
```

These directories must be available to IntelliSense when working with Arduino firmware.

---

## 05 — AVR Header Files

The AVR toolchain provides hardware-specific headers through AVR libc.

### Common headers

```cpp
#include <avr/io.h>
#include <avr/interrupt.h>
```

| Header | Function |
|---|---|
| `avr/io.h` | MCU register definitions, ports, timers, ADC, UART and peripheral registers |
| `avr/interrupt.h` | Interrupt definitions, ISR macros and interrupt control |
| `Arduino.h` | Arduino Core definitions, functions, pin mappings and Arduino API |

These headers are provided by different components:

| Header | Provider |
|---|---|
| `avr/io.h` | AVR toolchain / AVR libc |
| `avr/interrupt.h` | AVR toolchain / AVR libc |
| `Arduino.h` | Arduino AVR Core |

---

## 06 — VS Code Configuration

### Required extension

Install the Microsoft C/C++ extension:

```text
ms-vscode.cpptools
```

Install through the command line:

```bash
code --install-extension ms-vscode.cpptools
```

### `c_cpp_properties.json`

The following configuration is verified for the current development environment.

File location:

```text
.vscode/c_cpp_properties.json
```

```json
{
    "configurations": [
        {
            "name": "Linux-GCC",
            "includePath": [
                "${workspaceFolder}/**",
                "/usr/share/arduino/hardware/arduino/avr/cores/arduino",
                "/usr/share/arduino/hardware/arduino/avr/variants/standard"
            ],
            "defines": [
                "F_CPU=16000000UL",
                "ARDUINO=10819",
                "ARDUINO_ARCH_AVR",
                "ARDUINO_AVR_UNO"
            ],
            "compilerPath": "/usr/bin/avr-g++",
            "compilerArgs": [
                "-mmcu=atmega328p"
            ],
            "cStandard": "gnu11",
            "cppStandard": "gnu++17",
            "intelliSenseMode": "gcc-x64"
        }
    ],
    "version": 4
}
```

### Configuration explanation

| Setting | Description |
|---|---|
| `includePath` | Local project files, Arduino Core headers and Uno variant headers |
| `defines` | Arduino platform definitions and CPU clock configuration |
| `compilerPath` | AVR C++ compiler used for IntelliSense environment discovery |
| `compilerArgs` | Target MCU selection |
| `cStandard` | GNU C11 |
| `cppStandard` | GNU C++17 |
| `intelliSenseMode` | GCC-compatible IntelliSense parsing mode |

> **Important:** `compilerPath` must point to `avr-g++`, not the host `/usr/bin/g++` or `/usr/bin/gcc`. The host compiler targets the Linux system, while the AVR compiler targets the ATmega328P.

---

## 07 — Compiler Verification

Verify that the compiler recognizes the selected target:

```bash
avr-g++ -mmcu=atmega328p -dM -E -x c++ /dev/null
```

Check the Arduino Core header:

```bash
ls /usr/share/arduino/hardware/arduino/avr/cores/arduino/Arduino.h
```

Check the Uno variant directory:

```bash
ls /usr/share/arduino/hardware/arduino/avr/variants/standard
```

Check AVR device headers:

```bash
ls /usr/lib/avr/include/avr/io.h
```

---

## 08 — IntelliSense Troubleshooting

If VS Code reports errors in Arduino or AVR headers:

### Reset IntelliSense

Open the Command Palette:

```text
Ctrl + Shift + P
```

Run:

```text
C/C++: Reset IntelliSense Database
```

If necessary, reload VS Code:

```text
Developer: Reload Window
```

### Verify the active configuration

Run:

```text
C/C++: Select IntelliSense Configuration
```

Select:

```text
Linux-GCC
```

### Common configuration mistakes

| Problem | Correct configuration |
|---|---|
| Host compiler selected | Use `/usr/bin/avr-g++` |
| MCU target not defined | Add `-mmcu=atmega328p` |
| `Arduino.h` not found | Add Arduino Core include path |
| Arduino pin definitions missing | Add Uno `variants/standard` path |
| AVR registers not recognized | Use AVR compiler and AVR libc headers |
| Incorrect CPU clock | Define `F_CPU=16000000UL` |
| Incorrect Arduino platform definitions | Define `ARDUINO`, `ARDUINO_ARCH_AVR` and `ARDUINO_AVR_UNO` |

---

## 09 — Host-Side C++ vs AVR Firmware

This project may contain both Linux-side tools and AVR firmware.

These programs use different compilers and must not share the same compiler configuration.

### Linux applications

Programs running on Ubuntu, such as serial communication utilities and host-side tools, use:

```text
/usr/bin/g++
```

Example compilation:

```bash
g++ -std=c++17 -Wall -Wextra -O2 serial_proxy.cpp -o serial_proxy -lutil
```

### Arduino firmware

Firmware running on the Arduino Uno uses:

```text
/usr/bin/avr-g++
```

Target:

```text
ATmega328P
```

Compiler argument:

```bash
-mmcu=atmega328p
```

The host compiler and AVR cross-compiler are not interchangeable.

---

## 10 — Environment Summary

```text
┌──────────────────────────────────────────────────────────┐
│                  AVR DEVELOPMENT STACK                  │
├──────────────────────────────────────────────────────────┤
│  HOST                                                  │
│  Ubuntu Linux                                           │
│                                                        │
│  HOST APPLICATIONS                                     │
│  /usr/bin/g++                                          │
│  Native x86_64 Linux                                   │
│                                                        │
│  AVR TOOLCHAIN                                         │
│  /usr/bin/avr-g++                                      │
│  Target: ATmega328P                                     │
│  Clock: 16 MHz                                          │
│                                                        │
│  AVR LIBRARY                                           │
│  avr-libc                                               │
│                                                        │
│  ARDUINO CORE                                          │
│  /usr/share/arduino/hardware/arduino/avr/cores/arduino │
│                                                        │
│  UNO VARIANT                                           │
│  /usr/share/arduino/hardware/arduino/avr/variants/standard│
│                                                        │
│  IDE                                                   │
│  Visual Studio Code                                    │
│  Microsoft C/C++ Extension                            │
└──────────────────────────────────────────────────────────┘
```

---

### ⚙️ Reference

This document describes the currently verified development environment for the Arduino Uno / ATmega328P project on Ubuntu Linux.

The Arduino firmware must be analyzed and compiled using the AVR toolchain, while Linux-side utilities must be compiled using the native Linux toolchain.