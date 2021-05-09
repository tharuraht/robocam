#!/usr/bin/env bash
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py
RTSP_PATH=$ROBOCAM_DIR/host_machine/rtsp_rec/

export GST_PLUGIN_PATH=/home/tharu/Downloads/latency-clock/

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

function close_upnp {
  echo "Closing upnp ports"
  python3 upnp_rtsp.py "CLOSE"
}

#Change working directory
cd $RTSP_PATH

trap "close_upnp; exit" INT TERM ERR # Trap and run on exit
trap 'kill 0' EXIT 

# Start programs
python3 ps_bitrate.py &    # Bitrate profiler and RTCP Stats
$GST_PATH  $RTSP_PATH/rtsp_server.py  &  # RTSP Streamer
open_upnp &                       # Upnp port generator
$ROBOCAM_DIR/host_machine/control/robot_joy_udp.py # Robot platform controller
wait

