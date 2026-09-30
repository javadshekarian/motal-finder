import subprocess
import time

frequency = 1000
duration = 0.2

while True:
    subprocess.run([
        "speaker-test",
        "-t", "sine",
        "-f", str(frequency),
        "-l", "1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(0.5)
