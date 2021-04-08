#!/usr/bin/bash

# Get current dir of script
script_dir="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Get arduino port                                        
port=`ls /dev/ttyUSB*`

$script_dir/robot_ser_relay.py $port
