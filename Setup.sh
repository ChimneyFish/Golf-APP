#!/bin/bash

echo "Setting up Raspberry Pi for Golf Range Finder & Scorekeeper..."

# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y gpsd gpsd-clients python3-gps minicom python3-pyqt6 python3-pyqt6.qtwebengine

# Install required Python libraries
wget https://files.pythonhosted.org/packages/75/24/1f575eb17a8135e54b3c243ff87e2f4d6b2389942836021d0628ed837559/pynmea2-1.19.0-py3-none-any.whl
pip3 install --user folium geopy requests pynmea2 --break-system-packages

# Enable and start GPS daemon
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Configure Raspberry Pi settings
echo "Configuring Raspberry Pi settings..."

# Modify /boot/config.txt
sudo tee -a /boot/config.txt <<EOF
dtparam=spi=on
dtoverlay=pi3-disable-bt
core_freq=250
enable_uart=1
force_turbo=1
EOF

# Backup and modify boot command line settings
sudo cp /boot/cmdline.txt /boot/cmdline_backup.txt
sudo tee /boot/cmdline.txt <<EOF
dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 
elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

# Disable serial console services
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service

sudo systemctl stop serial-getty@ttys0.service
sudo systemctl disable serial-getty@ttys0.service

# Enable UART
sudo systemctl enable serial-getty@ttys0.service

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
tee ~/.config/autostart/golf_range_finder.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=python3 /home/pi/Golf-APP/main_gui.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Golf Range Finder
EOF

# Reboot to apply changes
echo "Setup complete. Rebooting now..."
sudo reboot
