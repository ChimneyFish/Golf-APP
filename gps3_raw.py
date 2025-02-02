import serial
import time

port = "/dev/ttyACM0"

with serial.Serial(port, baudrate=9600, timeout=1) as ser:
    while True:
        newdata = ser.readline().decode("utf-8", errors="ignore").strip()
        print("Raw Data:", newdata)  # Print everything received from GPS
        time.sleep(1)
