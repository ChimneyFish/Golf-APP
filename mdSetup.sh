#!/bin/bash

echo "Setting up Raspberry Pi for AI-Caddy on PiOS-Lite..."
sleep 2

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

### --- CREATE ADMIN USER IF NEEDED ---
if id "admin" &>/dev/null; then
    echo "User 'admin' exists."
else
    echo "Creating user 'admin' with password 'admin'..."
    sudo adduser --disabled-password --gecos "" admin
    echo "admin:admin" | sudo chpasswd
    sudo usermod -aG sudo admin
fi

### --- COPY GOLF-APP SAFELY ---
if [ -d "$DIR/Golf-APP" ]; then
    echo "Copying Golf-APP to /home/admin/Golf-APP"
    sudo rm -rf /home/admin/Golf-APP
    sudo mkdir -p /home/admin/Golf-APP
    sudo cp -r "$DIR/Golf-APP/"* /home/admin/Golf-APP/
    sudo chown -R admin:admin /home/admin/Golf-APP
else
    echo "ERROR: Golf-APP folder not found in installer directory!"
    exit 1
fi

sudo chmod +x /home/admin/Golf-APP/main.py

### --- UPDATE SYSTEM ---
sudo apt update && sudo apt upgrade -y

### --- INSTALL MINIMAL DESKTOP + PYQT ---
sudo apt install -y \
    xorg openbox lightdm \
    python3-pip python3-pyqt5 python3-pyqt5.qtwebengine \
    xserver-xorg-input-evdev x11-xserver-utils \
    minicom

### --- PYTHON DEPENDENCIES (NO PyQt5 HERE) ---
sudo pip3 install folium geopy requests pynmea2 gpsd-py3 pyserial --break-system-packages

### --- ENABLE UART + DISABLE BLUETOOTH ---
sudo sed -i '/enable_uart/d' /boot/firmware/config.txt
sudo sed -i '/dtoverlay=pi3-disable-bt/d' /boot/firmware/config.txt

sudo tee -a /boot/firmware/config.txt >/dev/null <<EOF
enable_uart=1
dtoverlay=pi3-disable-bt
dtparam=spi=on
core_freq=250
force_turbo=1
EOF

### --- FIX CMDLINE.TXT (REPLACE SAFELY) ---
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline_backup.txt
CMDLINE=$(head -n1 /boot/firmware/cmdline.txt)

sudo tee /boot/firmware/cmdline.txt >/dev/null <<EOF
$CMDLINE dwc_otg.lpm_enable=0 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

### --- DISABLE SERIAL CONSOLE ---
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

### --- PERMISSIONS FOR SERIAL ---
sudo usermod -aG dialout admin
sudo usermod -aG tty admin

### --- FIX PERMISSIONS AT BOOT ---
( sudo crontab -l 2>/dev/null; echo "@reboot chown admin:admin /dev/ttyAMA0" ) | sudo crontab -

### --- LIGHTDM AUTOLOGIN ---
sudo tee /etc/lightdm/lightdm.conf >/dev/null <<EOF
[Seat:*]
autologin-user=admin
autologin-session=openbox
autologin-user-timeout=0
EOF

### --- OPENBOX AUTOSTART FOR PYTHON APP ---
sudo -u admin mkdir -p /home/admin/.config/openbox

sudo -u admin tee /home/admin/.config/openbox/autostart >/dev/null <<EOF
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/admin/.Xauthority
/usr/bin/python3 /home/admin/Golf-APP/main.py &
EOF

sudo chmod +x /home/admin/.config/openbox/autostart

### --- ENABLE LIGHTDM ---
sudo systemctl enable lightdm

echo "Setup complete. Rebooting..."
sleep 3
sudo reboot
