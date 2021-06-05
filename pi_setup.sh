#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`
export GST_PLUGIN_PATH="/home/pi/Documents/latency-clock"
GST_PATH=`python3 utils/parse_json.py pi "gst_path"`
# export GST_DEBUG=timestampoverlay:5,timeoverlayparse:5
# export GST_DEBUG=4

# Mount USB
sudo mount -o umask=0 /dev/sda1 /media/usb  && echo "Mounted USB Drive"

$GST_PATH robot/start.py
