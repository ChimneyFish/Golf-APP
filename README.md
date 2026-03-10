# Golf-APP
Python Based application To run on Raspberrypi that will act as a Rangefinder, drive distance calculator, and club suggestion caddy, as you play it learns how far you hit each club and will start to suggest a club to use based on the distance to the pin.  Will have a save course feature that will be saved in json format so eventually this repository will have a json file for many courses and you will not have to do the leg work.

## Installation
1. Clone this repository onto your Raspberry Pi
2. ```cd Golf-APP && Chmod +x setup-rpiOS.sh```
3. ```sudo sh Setup.sh```

# Hardware
 1. Raspberry Pi (doesn't matter which one, Pi's 3 and above are preferred)
 2. GPS Module ([This is what I used](https://www.amazon.com/dp/B0B49LB18G?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1))
 3. touch screen of some sorts to act as the interactive display

 # Hardware setup
 The GPS module connects `+` to `pin 2` of the pi, `-` to `pin 6` of the pi, and `tx` to `pin 10` of the pi. 

 **Please note, this setup is assuming that the Raspberry pie SD card will only be used to run this Application as it changes the overlays and functionality of the boot process within the OS.**

## This is still in the works and very buggy!


