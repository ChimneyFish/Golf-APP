import socket
import time
import json
import pynmea2
import serial

port = "/dev/ttyAMA0"

def get_gps_data():
    try:
        with serial.Serial(port, baudrate=9600, timeout=0.5) as ser:
            while True:
                newdata = ser.readline().decode("utf-8", errors="ignore").strip()
                if newdata.startswith("$GPRMC"):
                    try:
                        newmsg = pynmea2.parse(newdata)
                        if newmsg.status == 'A':  # Data Valid
                            lat = newmsg.latitude
                            lng = newmsg.longitude
                            return {'latitude': lat, 'longitude': lng}
                    except pynmea2.ParseError:
                        continue  # Ignore parsing errors
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return None

def start_gps_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 5000))  # Bind to localhost:5000
    server_socket.listen(1)
    print("GPS Server started, waiting for connections...")

    while True:
        conn, addr = server_socket.accept()
        print(f"Client connected from {addr}")

        try:
            while True:
                gps_data = get_gps_data()
                if gps_data:
                    conn.sendall(json.dumps(gps_data).encode('utf-8') + b'\n')
                else:
                    conn.sendall(json.dumps({'error': 'GPS data unavailable'}).encode('utf-8') + b'\n')
                time.sleep(2)  # Simulate delay in GPS updates
        except BrokenPipeError:
            print("Client disconnected.")
        finally:
            conn.close()

if __name__ == "__main__":
    start_gps_server()
