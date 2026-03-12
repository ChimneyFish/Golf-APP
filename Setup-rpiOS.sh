#!/bin/bash

echo "Configuring Raspberry Pi UART for GPS module..."
sleep 2

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
sleep 5

sudo apt install -y python3-pip minicom python3-pyqt5 python3-pyqt5.qtwebkit
sleep 2

sudo pip3 install folium geopy requests pynmea2 PyQt5 pynmea2 pyserial --break-system-packages
sleep 2

sudo mkdir -p ~/.config/autostart
sudo tee ~/.config/autostart/golf-app.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Golf Range Finder
Exec=/usr/bin/python3 /home/admin/Golf-APP/main.py
Icon=/home/admin/Golf-APP/icon.png
Comment=Start Golf Range Finder & Scorekeeper
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

sleep 2

# Add admin to UART groups
sudo usermod -aG dialout admin
sudo usermod -aG tty admin

sudo chmod 644 ~/.config/autostart/golf-app.desktop

# Enable UART and disable Bluetooth
sudo sed -i '/enable_uart/d' /boot/firmware/config.txt
sudo sed -i '/dtoverlay=pi3-disable-bt/d' /boot/firmware/config.txt

echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
echo "dtoverlay=pi3-disable-bt" | sudo tee -a /boot/firmware/config.txt

# Disable serial console
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

sudo systemctl stop serial-getty@ttyS0.service
sudo systemctl disable serial-getty@ttyS0.service
sudo systemctl mask serial-getty@ttyS0.service

echo "UART configured. Rebooting now..."
sleep 3
sudo reboot
