#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`
export GST_PLUGIN_PATH="/home/pi/Documents/latency-clock"
GST_PATH=`python3 utils/parse_json.py pi "gst_path"`
GPS_PORT=`python3 utils/parse_json.py pi "gps_port"`
# export GST_DEBUG=timestampoverlay:5,timeoverlayparse:5
# export GST_DEBUG=4

# Mount USB
sudo mount -o umask=0 /dev/sda1 /media/usb  && echo "Mounted USB Drive"

# Connect GPSD to GPS
# https://unix.stackexchange.com/questions/66901/how-to-bind-usb-device-under-a-static-name
sudo killall gpsd
sudo gpsd $GPS_PORT -F /var/run/gpsd.sock

$GST_PATH robot/start.py
