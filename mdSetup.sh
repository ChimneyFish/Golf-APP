#!/bin/bash

echo "Setting up Raspberry Pi for AI-Caddy with minimal Desktop for better performance..."
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
sudo apt install -y python3-pip xserver-xorg gpsd gpsd-clients python3-gps minicom python3-pyqt5 python3-pyqt5.qtwebengine
sudo apt install xserver-xorg-input-mutouch xserver-xorg-input-evdev  xserver-xorg-input-multitouch xserver-xorg-dev x11-xserver-utils
sudo aot install openbox xorg

sudo pip3 install folium geopy requests pynmea2 PyQt5 gpsd-py3 pynmea2 pyserial  --break-system-packages
pip3 install --user folium geopy requests pynmea2 PyQt5 gpsd-py3 pynmea2 pyserial  --break-system-packages
# Enable and start GPS daemon
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Configure Raspberry Pi settings
echo "Configuring Raspberry Pi settings..."
sleep 5
# Modify /boot/config.txt
sudo tee -a /boot/firmware/config.txt <<EOF
dtparam=spi=on
dtoverlay=pi3-disable-bt
core_freq=250
enable_uart=1
force_turbo=1
EOF

# Backup and modify boot command line settings
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline_backup.txt
sudo tee -a /boot/firmware/cmdline.txt <<EOF
dwc_otg.lpm_enable=0 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles
EOF

# Disable serial console services
sudo systemctl stop serial-getty@ttyAMA0.service
sudo systemctl disable serial-getty@ttyAMA0.service
sudo systemctl mask serial-getty@ttyAMA0.service

sudo systemctl stop serial-getty@ttys0.service
sudo systemctl disable serial-getty@ttys0.service

# Enable UART
sudo systemctl enable serial-getty@ttys0.service

sudo usermod -aG dialout admin
sudo usermod -aG tty admin
sudo chown admin:admin /dev/ttyAMA0

#set up Minimal Desktop for Application
sudo apt install lightdm openbox
sudo tee -a /etc/lightdm/lightdm.conf <<EOF
[Seat:*]
autologin-user=admin
autologin-session=openbox
EOF

mkdir -p ~/.config/openbox
tee ~/.config/openbox/autostart <<EOF
#!/bin/bash
/usr/bin/python3 /home/admin/Golf-APP/main.py &
EOF

sudo systemctl enable lightdm
sudo systemctl start lightdm

# Set up permissions at reboot
echo "@reboot sudo chown admin:admin /dev/ttyAMA0" | sudo crontab -e

# Reboot to apply changes
echo "Setup complete. please Rebooting now..."
sleep 5
sudo reboot