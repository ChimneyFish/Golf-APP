#!/bin/bash

echo "Setting up Raspberry Pi for Golf Range Finder & Scorekeeper..."

# Update package list
sudo apt update

# Install required system packages
sudo apt-get install gpsd gpsd-clients python3-gps python3-pip -y

# Fix broken installs if any
sudo apt --fix-broken install -y

# Install required Python libraries
pip3 install geopy gpsd-py3 PyQt6

# Ensure Python3 is installed
sudo apt-get install python3 -y

# Configure Raspberry Pi settings
echo "Configuring Raspberry Pi settings..."

# Enable the GPS module
sudo systemctl enable gpsd
sudo systemctl start gpsd
sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock

# Modify /boot/config.txt
sudo tee -a /boot/config.txt <<EOF
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=pi3-disable-bt
core_freq=250
enable_uart=1
force_turbo=1
EOF

# Disable serial console to avoid conflicts with GPS module
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service

# Backup and modify boot command line settings
sudo cp /boot/cmdline.txt /boot/cmdline_backup.txt
sudo tee /boot/cmdline.txt <<EOF
dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

# Create GPS reading script
sudo tee /opt/gps.py <<EOF
import serial
import time
import pynmea2

port = "/dev/ttyAMA0"

while True:
    with serial.Serial(port, baudrate=9600, timeout=0.5) as ser:
        newdata = ser.readline().decode("utf-8", errors="ignore").strip()
        if newdata.startswith("\$GPRMC"):
            try:
                newmsg = pynmea2.parse(newdata)
                lat = newmsg.latitude
                lng = newmsg.longitude
                print(f"Latitude: {lat}, Longitude: {lng}")
            except pynmea2.ParseError:
                print("Error parsing GPS data")
    time.sleep(1)
EOF

# Make GPS script executable
sudo chmod +x /opt/gps.py

# Set up autostart for Golf Range Finder GUI
mkdir -p ~/.config/autostart
tee ~/.config/autostart/Golf-Caddy.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=python3 /home/admin/Golf-APP/main.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Golf-Caddy
EOF

echo "Setup complete! Reboot your Raspberry Pi for the changes to take effect."


# Reboot to apply changes
echo "Setup complete. Rebooting now..."
sudo reboot
