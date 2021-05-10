#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`
export GST_PLUGIN_PATH="/home/pi/Downloads/latency-clock"
GST_PATH=/home/pi/Downloads/gst-build/gst-env.py

$GST_PATH robot/start.py
