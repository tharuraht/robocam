#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`

# host_machine/start.sh
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py
export GST_PLUGIN_PATH=/home/tharu/Documents/latency-clock/

$GST_PATH host_machine/start.py
