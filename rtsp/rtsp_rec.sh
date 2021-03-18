gst-launch-1.0 -v rtspsrc location=rtsp://192.168.0.106:8554/test latency=0 buffer-mode=auto ! decodebin ! videoconvert ! autovideosink sync=false
