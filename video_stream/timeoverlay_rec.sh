#!/bin/bash
export GST_PLUGIN_PATH="/home/tharu/Documents/latency-clock"

# tcpclientsrc host=10.200.200.2 port=5000 \
GST_DEBUG=timeoverlayparse:5 gst-launch-1.0 \
udpsrc port=5000 \
! gdpdepay \
! rtph264depay \
! decodebin \
! timeoverlayparse \
! videoconvert \
! autovideosink sync=false
