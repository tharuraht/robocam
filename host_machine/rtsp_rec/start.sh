#!/usr/bin/env bash
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py


if [ ! -f robocam_rec ] 
then
  echo "robocam_rec doesn't exist, compiling..."
  gcc  `pkg-config --cflags --libs gstreamer-rtsp-server-1.0` -o robocam_rec robocam_rec.c
fi
echo $PIPELINE
(trap 'kill 0' SIGINT; python3 stat_send.py \
& $GST_PATH `realpath robocam_rec` " \
        (rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink)" )
