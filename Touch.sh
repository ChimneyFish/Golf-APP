#!bin/bash

sudo apt update && sudo apt upgrade -y
sudo apt install build-essential xinput evtest
sudo tee -a /boot/armbianEnv.txt <<EOF
overlays=spi-spidev
param_spidev_spi_bus=0
param_spidev_spi_cs=1
EOF

mkdir ads7846 && cd ads7846
wget https://raw.githubusercontent.com/raspberrypi/linux/rpi-3.6.y/drivers/input/touchscreen/ads7846.c || { echo "Download failed"; exit 1; }

tee Makefile <<EOF
obj-m := ads7846.o
KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)
all:
    $(MAKE) -C $(KDIR) M=$(PWD) modules
clean:
    $(MAKE) -C $(KDIR) M=$(PWD) clean
install:
    $(MAKE) -C $(KDIR) M=$(PWD) modules_install
EOF

sudo make
sudo make install
sudo depmod
sudo tee -a /etc/modules-load.d/ads7846.conf <<EOF
ads7846
ads7846_device
EOF
