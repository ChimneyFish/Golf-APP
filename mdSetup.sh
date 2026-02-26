#!/bin/bash

echo "Setting up Raspberry Pi for AI-Caddy with minimal Desktop..."
sleep 3

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

### --- MOVE APP DIRECTORY SAFELY ---
if [ ! -d "/home/admin/Golf-APP" ]; then
    echo "Moving Golf-APP to /home/admin/Golf-APP"
    sudo mkdir -p /home/admin/Golf-APP
    sudo cp -r "$DIR"/* /home/admin/Golf-APP/
    sudo chown -R admin:admin /home/admin/Golf-APP
else
    echo "Golf-APP already exists."
fi

### --- UPDATE SYSTEM ---
sudo apt update && sudo apt upgrade -y

### --- INSTALL REQUIRED PACKAGES ---
sudo apt install -y \
    python3-pip xserver-xorg gpsd gpsd-clients python3-gps minicom \
    python3-pyqt5 python3-pyqt5.qtwebengine \
    xserver-xorg-input-mutouch xserver-xorg-input-evdev \
    xserver-xorg-input-multitouch xserver-xorg-dev x11-xserver-utils \
    openbox xorg lightdm

### --- PYTHON DEPENDENCIES ---
sudo pip3 install folium geopy requests pynmea2 PyQt5 gpsd-py3 pyserial --break-system-packages

### --- ENABLE GPSD ---
sudo systemctl enable gpsd
sudo systemctl start gpsd

### --- MODIFY /boot/firmware/config.txt ---
sudo tee -a /boot/firmware/config.txt >/dev/null <<EOF
dtparam=spi=on
dtoverlay=pi3-disable-bt
core_freq=250
enable_uart=1
force_turbo=1
EOF

### --- FIX CMDLINE.TXT (REPLACE, DO NOT APPEND) ---
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline_backup.txt
CMDLINE=$(head -n1 /boot/firmware/cmdline.txt)
sudo tee /boot/firmware/cmdline.txt >/dev/null <<EOF
$CMDLINE dwc_otg.lpm_enable=0 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

### --- SERIAL CONFIG ---
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

sudo usermod -aG dialout admin
sudo usermod -aG tty admin

### --- FIX PERMISSIONS AT BOOT ---
( sudo crontab -l 2>/dev/null; echo "@reboot chown admin:admin /dev/ttyAMA0" ) | sudo crontab -

### --- LIGHTDM AUTOLOGIN ---
sudo tee /etc/lightdm/lightdm.conf >/dev/null <<EOF
[Seat:*]
autologin-user=admin
autologin-session=openbox
EOF

### --- OPENBOX AUTOSTART FOR PYTHON APP ---
sudo -u admin mkdir -p /home/admin/.config/openbox
sudo -u admin tee /home/admin/.config/openbox/autostart >/dev/null <<EOF
#!/bin/bash
/usr/bin/python3 /home/admin/Golf-APP/main.py &
EOF
sudo chmod +x /home/admin/.config/openbox/autostart

### --- ENABLE LIGHTDM ---
sudo systemctl enable lightdm
sudo systemctl start lightdm

echo "Setup complete. Rebooting..."
sleep 3
sudo reboot
