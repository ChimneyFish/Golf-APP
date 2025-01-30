#!bin/bash/
read "Password for priviledged user aka sudoer" PASSWORD
sudo apt update
echo "$PASSWORD"
sudo apt install -y gpsd gpsd-clients python3-gps
pip3 install PyQt5 folium geopy requests --break-system-packages
sudo systemctl enable gpsd
sudo systemctl start gpsd