#!/bin/bash

echo "Setting up Raspberry Pi for Golf Range Finder & Scorekeeper..."

# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y gpsd gpsd-clients python3-gps minicom python3-pyqt5 python3-pyqt5.qtwebengine

# Install required Python libraries
pip3 install --user folium geopy requests pynmea2 PyQt6 gpsd-py3 pynmea2 pyserial  --break-system-packages

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


# Make GPS script executable


# Set up autostart for Golf Range Finder GUI
mkdir -p ~/.config/autostart
tee ~/.config/autostart/golf_range_finder.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=python3 /home/admin/Golf-APP/main.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Golf Range Finder
EOF

# Reboot to apply changes
echo "Setup complete. please Rebooting now..."

