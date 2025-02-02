import serial
import time
import pynmea2

port = "/dev/ttyACM0"

while True:
    try:
        with serial.Serial(port, baudrate=9600, timeout=0.5) as ser:
            newdata = ser.readline().decode("utf-8", errors="ignore").strip()
            if newdata.startswith("$GPRMC"):  # Removed unnecessary backslash
                try:
                    newmsg = pynmea2.parse(newdata)
                    lat = newmsg.latitude
                    lng = newmsg.longitude
                    print(f"Latitude: {lat}, Longitude: {lng}")
                except pynmea2.ParseError:
                    print("Error parsing GPS data")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    
    time.sleep(1)
