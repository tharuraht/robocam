gst-launch-1.0 tcpserversrc host=192.168.0.79 port=5000 ! matroskademux ! decodebin ! videoconvert ! autovideosink sync=false
