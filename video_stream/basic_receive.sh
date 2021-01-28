#!/bin/bash
gst-launch-1.0 tcpclientsrc host=192.168.0.101 port=5000 \
! matroskademux \
! decodebin \
! videoconvert \
! autovideosink sync=false
