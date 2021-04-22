#RTSP_PATH=~/Downloads/gst-rtsp-server-1.14.4/examples/test-record 
RTSP_PATH=./robocam_rec

$RTSP_PATH -p 5000 "(rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink)"
