#!/usr/bin/env bash
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py
RTSP_PATH=$ROBOCAM_DIR/host_machine/rtsp_rec/

export GST_PLUGIN_PATH=/home/tharu/Documents/latency-clock/
# export GST_DEBUG=timeoverlayparse:5

#Change working directory
cd $RTSP_PATH

function open_upnp {
# echo "Opening upnp ports"
res=$(lsof -i4 -n | grep python | grep UDP) 
while true
do
  while  [ -z "$res" ]
  do
    res=$(lsof -i4 -n | grep python | grep UDP) 
    sleep 0.5 # wait half a second
  done
  python3 upnp_rtsp.py "SETUP" "$res"
  res=""
  sleep 1
done
}

function cleanup {
  echo "Closing upnp ports"
  python3 upnp_rtsp.py "CLOSE"
  # rm -r tmp
}


trap "cleanup; exit" INT TERM ERR # Trap and run on exit
trap 'kill 0' EXIT

# Create temp directory
mkdir -p tmp

# Start programs
python3 ps_bitrate.py &    # Bitrate profiler and RTCP Stats
$GST_PATH  $RTSP_PATH/rtsp_server.py  &  # RTSP Streamer
open_upnp &                       # Upnp port generator
$ROBOCAM_DIR/host_machine/control/robot_control.py # Robot platform controller
wait

