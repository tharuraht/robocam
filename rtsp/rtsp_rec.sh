RTSP_PROPS=latency=0 buffer-mode=auto drop-on-latency=true do-retransmission=false

gst-launch-1.0 -v rtspsrc location=rtsp://10.200.200.2:8554/test $RTSP_PROPS! \
	decodebin ! videoconvert ! autovideosink sync=false
