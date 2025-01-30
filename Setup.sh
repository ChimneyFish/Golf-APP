#!/bin/bash

# Update package lists
sudo apt update

# Install necessary GPS packages
sudo apt install -y gpsd gpsd-clients python3-gps

# Install Python dependencies
pip3 install --user PyQt5 folium geopy requests pynmea2

# Enable and start GPS daemon
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Append required configurations to /boot/config.txt
sudo tee -a /boot/config.txt <<EOF
dtparam=spi=on
dtoverlay=pi3-disable-bt
core_freq=250
enable_uart=1
force_turbo=1
EOF

# Backup and modify cmdline.txt
sudo cp /boot/cmdline.txt /boot/cmdline_backup.txt
sudo tee -a /boot/cmdline.txt <<EOF
dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 
elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

# Disable default serial console services
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service

sudo systemctl stop serial-getty@ttys0.service
sudo systemctl disable serial-getty@ttys0.service

# Enable serial on ttys0
sudo systemctl enable serial-getty@ttys0.service

# Install minicom and pynmea2
sudo apt install -y minicom python3-pynmea2

# Create GPS Python script
sudo tee /opt/gps.py <<EOF
import serial
import time
import pynmea2

port = "/dev/ttyAMA0"
ser = serial.Serial(port, baudrate=9600, timeout=0.5)

while True:
    newdata = ser.readline().decode('ascii', errors='replace').strip()
    if newdata.startswith("\$GPRMC"):
        try:
            newmsg = pynmea2.parse(newdata)
            lat = newmsg.latitude
            lng = newmsg.longitude
            gps_data = f"Latitude={lat} and Longitude={lng}"
            print(gps_data)
        except pynmea2.ParseError:
            print("Error parsing NMEA data")
    time.sleep(1)
EOF

# Make GPS script executable
sudo chmod +x /opt/gps.py

