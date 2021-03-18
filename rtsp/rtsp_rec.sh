gst-launch-1.0 -v rtspsrc location=rtsp://10.200.200.2:8554/test latency=0 buffer-mode=auto ! decodebin ! videoconvert ! autovideosink sync=false
