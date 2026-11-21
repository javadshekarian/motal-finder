import serial

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

ser = serial.Serial(
    PORT,
    BAUDRATE,
    timeout=2
)

ser.reset_input_buffer()

data = ser.read(128)

print("HEX:", data.hex(" "))

for i in range(0, len(data), 2):

    if i + 1 >= len(data):
        break

    packet = (
        data[i]
        | (data[i + 1] << 8)
    )

    adc = packet & 0x03FF
    phase = (packet >> 10) & 0x3F

    print(
        f"{i // 2 + 1:02d}: "
        f"bytes={data[i]:02X} {data[i + 1]:02X} | "
        f"packet={packet:04X} | "
        f"ADC={adc} | "
        f"PHASE={phase}"
    )

ser.close()