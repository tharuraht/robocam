#!/usr/bin/env bash
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py
RTSP_PATH=$ROBOCAM_DIR/host_machine/rtsp_rec/

#Change working directory
cd $RTSP_PATH

trap "close_upnp; exit" INT TERM ERR
trap 'kill 0' EXIT 

function open_upnp {
echo "Opening upnp ports"

res=$(lsof -i4 -n | grep robo | grep UDP) 
while true
do
  while  [ -z "$res" ]
  do
    res=$(lsof -i4 -n | grep robo | grep UDP) 
    sleep 0.5 # wait half a second
  done
  # echo "found it!"
  # echo $res
  python3 upnp_rtsp.py "SETUP" "$res"

  res=""
  sleep 1
done
}

function close_upnp {
  echo "Closing upnp ports"
  python3 upnp_rtsp.py "CLOSE"
}

if [ ! -f robocam_rec ] 
then
  echo "robocam_rec doesn't exist, compiling..."
  make
fi


# python3 stat_send.py &            # RTCP Stat Sender
python3 ps_bitrate.py &
$GST_PATH python3 $RTSP_PATH/../receiver/rtsp_server.py  &         # RTSP Streamer
open_upnp &                       # Upnp port generator
python3 $ROBOCAM_DIR/host_machine/control/robot_joy_udp.py & # Robot platform controller
wait

