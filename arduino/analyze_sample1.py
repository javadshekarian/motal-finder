
import struct
import matplotlib.pyplot as plt

with open("BASE.bin", "rb") as f:
    values = struct.unpack("<16000H", f.read())

sample1 = [values[i * 16 + 1] for i in range(1000)]

plt.figure(figsize=(14, 5))
plt.plot(sample1, linewidth=0.8)
plt.xlabel("Wave number")
plt.ylabel("ADC value")
plt.title("Sample 01 - 1000 waves")
plt.grid(True)
plt.tight_layout()
plt.savefig("sample1.png", dpi=150)
plt.show()
