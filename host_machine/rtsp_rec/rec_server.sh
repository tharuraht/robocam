#RTSP_PATH=~/Downloads/gst-rtsp-server-1.14.4/examples/test-record 
RTSP_PATH=/home/tharu/Documents/robocam/host_machine/rtsp_rec/robocam_rec
GST_PATH=/home/tharu/Downloads/gst-build/gst-env.py
PIPELINE="\"(rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink)\""

echo $PIPELINE
$GST_PATH $RTSP_PATH -p 5000 "(rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink)"
