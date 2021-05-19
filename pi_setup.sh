#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`
export GST_PLUGIN_PATH="/home/pi/Documents/latency-clock"
GST_PATH=/home/pi/Downloads/gst-build/gst-env.py
# export GST_DEBUG=timestampoverlay:5,timeoverlayparse:5
# export GST_DEBUG=4

$GST_PATH robot/start.py
