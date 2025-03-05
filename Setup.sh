#!/bin/bash

echo "Setting up Raspberry Pi for Golf Range Finder & Scorekeeper..."
sleep 5
# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y gpsd gpsd-clients python3-gps minicom python3-pyqt5 python3-pyqt5.qtwebengine

# Install required Python libraries
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

sudo systemctl stop serial-getty@ttys0.service
sudo systemctl disable serial-getty@ttys0.service

# Enable UART
sudo systemctl enable serial-getty@ttys0.service

# Set up autostart for Golf Range Finder GUI

sudo tee /etc/systemd/system/golf-app.service: <<EOF
[Unit]
Description=Golf Range Finder & Scorekeeper
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/admin/Golf-APP/main.py
WorkingDirectory=/home/admin/Golf-APP
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root
Environment=DISPLAY=:0
Environment=XAUTHORITY=/root/.Xauthority

[Install]
WantedBy=multi-user.target
EOF

sudo tee -a /root/.xinitrc <<EOF
#!/bin/sh
exec /usr/bin/python3 /home/admin/Golf-APP/main.py
EOF

sudo chmod +x /root/.xinitrc
sudo systemctl set-default graphical.target


# Ensure the .desktop file has the correct permissions
sudo systemctl enable golf-app.service
sudo systemctl start golf-app.service
# Additional setup

# Reboot to apply changes
echo "Setup complete. please Rebooting now..."
sleep 5
sudo reboot
