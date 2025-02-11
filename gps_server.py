import socket
import time
import json
import pynmea2
import serial

def start_gps_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 5000))  # Bind to localhost:5000
    server_socket.listen(1)
    print("GPS Server started, waiting for connections...")

    conn, addr = server_socket.accept()
    print(f"Client connected from {addr}")

    try:
        while True:
            # Simulated GPS data
            conn.sendall(json.dumps(gps_data).encode('utf-8') + b'\n')
            time.sleep(2)  # Simulate delay in GPS updates
    except BrokenPipeError:
        print("Client disconnected.")
    finally:
        conn.close()
        server_socket.close()

if __name__ == "__main__":
    start_gps_server()

port="/dev/ttyAMA0"    
def gps_data():
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