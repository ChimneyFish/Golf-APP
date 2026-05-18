#!/bin/bash

echo "Configuring Raspberry Pi UART for GPS module..."
sleep 2

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Create User
if id "admin" &>/dev/null; then
    echo "User 'admin' exists."
else
    echo "User 'admin' does not exist. Creating user 'admin'...Password is 'admin'"
    sudo adduser --disabled-password --gecos "" admin
    echo "admin:admin" | sudo chpasswd
    sudo usermod -aG sudo admin
fi

# 2. Move App Directory safely (using rsync to catch hidden files)
if [ ! -d "/home/admin/Golf-APP" ]; then
    echo "Moving Golf-APP repository to /home/admin/Golf-APP"
    sudo mkdir -p /home/admin/Golf-APP
    # rsync is safer than mv /* as it includes hidden files
    sudo rsync -a "$DIR"/ /home/admin/Golf-APP/
    sudo chown -R admin:admin /home/admin/Golf-APP
else
    echo "Golf-APP directory already exists in /home/admin/"
fi

# 3. Update & Install System Dependencies
sudo apt update && sudo apt upgrade -y
sleep 5

# python3-pyqt5 installed here handles the GUI
sudo apt install -y python3-pip minicom python3-pyqt5 python3-pyqt5.qtwebengine rsync
sleep 2

# Removed PyQt5 and duplicate pynmea2 from this list
sudo pip3 install folium geopy requests pynmea2 pyserial --break-system-packages
sleep 2

# 4. Setup Autostart for the 'admin' user explicitly
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

# Fix ownership and permissions for the autostart file
sudo chown -R admin:admin /home/admin/.config
sudo chmod 644 /home/admin/.config/autostart/golf-app.desktop
sleep 2

# 5. Add admin to UART groups
sudo usermod -aG dialout admin
sudo usermod -aG tty admin

# 6. Configure UART and Bluetooth in config.txt
sudo sed -i '/enable_uart/d' /boot/firmware/config.txt
sudo sed -i '/dtoverlay=disable-bt/d' /boot/firmware/config.txt
sudo sed -i '/dtoverlay=pi3-disable-bt/d' /boot/firmware/config.txt # Clean up legacy entry if it exists

echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt

# 7. Remove Boot Console from cmdline.txt (Critical for clean GPS data)
sudo sed -i 's/console=serial0,115200 //g' /boot/firmware/cmdline.txt
sudo sed -i 's/console=ttyAMA0,115200 //g' /boot/firmware/cmdline.txt

# 8. Disable serial console services
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

sudo systemctl stop serial-getty@ttyS0.service
sudo systemctl disable serial-getty@ttyS0.service
sudo systemctl mask serial-getty@ttyS0.service

echo "UART configured. Rebooting now..."
sleep 3
sudo reboot
