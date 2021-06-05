#!/usr/bin/env bash

export ROBOCAM_DIR=`realpath .`
GST_PATH=`python3 utils/parse_json.py host "gst_path"`
export GST_PLUGIN_PATH=/home/tharu/Documents/latency-clock/

$GST_PATH host_machine/start.py
