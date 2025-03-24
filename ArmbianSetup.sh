#!/bin/bash

echo "Setting up OrangePi for Golf Range Finder & Scorekeeper..."
sleep 5

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if id "admin" &>/dev/null; then
    echo "User 'admin' exists."
else
    echo "User 'admin' does not exist. Creating user 'admin'...Password is 'admin'"
    sudo adduser --disabled-password --gecos "" admin
    echo "admin:admin" | sudo chpasswd
    sudo usermod -aG sudo admin
fi

if [ ! -d "/home/admin/Golf-APP" ]; then
    echo "Moving Golf-APP repository to /home/admin/Golf-APP"
    sudo mkdir -p /home/admin/Golf-APP
    sudo mv "$DIR"/* /home/admin/Golf-APP/
    sudo chown -R admin:admin /home/admin/Golf-APP
else
    echo "Golf-APP directory already exists in /home/admin/"
fi

# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip gpsd gpsd-clients python3-gps minicom python3-pyqt5 python3-pyqt5.qtwebengine

# Install required Python libraries
sudo pip3 install folium geopy requests pynmea2 PyQt5 gpsd-py3 pynmea2 pyserial  --break-system-packages
pip3 install --user folium geopy requests pynmea2 PyQt5 gpsd-py3 pynmea2 pyserial  --break-system-packages

# Enable and start GPS daemon
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Configure OrangePi settings
echo "Configuring OrangePi settings..."
sleep 5

# Modify boot environment (specific to Armbian/OrangePi)
sudo tee -a /boot/armbianEnv.txt <<EOF
overlays=spi-spidev
param_uart2_rtscts=1
EOF

# Set permissions for serial ports
sudo usermod -aG dialout admin
sudo usermod -aG tty admin
sudo chown admin:admin /dev/ttyS1

# Set up autostart for Golf Range Finder GUI
sudo mkdir -p /home/admin/.config/autostart
sudo tee /home/admin/.config/autostart/golf-app.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Golf Range Finder
Exec=/usr/bin/python3 /home/admin/Golf-APP/main.py
Icon=/home/admin/Golf-APP/icon.png
Comment=Start Golf Range Finder & Scorekeeper
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

# Ensure the .desktop file has the correct permissions
sudo chmod 644 /home/admin/.config/autostart/golf-app.desktop

# Set up permissions at reboot
echo "@reboot sudo chown admin:admin /dev/ttyS1" | sudo crontab -e 

# Reboot to apply changes
echo "Setup complete. Please rebooting now..."
sleep 5
sudo reboot
