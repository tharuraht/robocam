gst-launch-1.0 rpicamsrc preview=false rotation=180 name=videosrc bitrate=2000000 \
! h264parse \
! video/x-h264,framerate=25/1,width=1280,height=720 \
! matroskamux \
! tcpclientsink host=192.168.0.79 port=5000
# ! tcpserversink host=192.168.0.101 port=5000 \


# # -v = verbose
# gst-launch-1.0 -c rpicamsrc preview=false bitrate=1000000 \
# ! h264parse \
# ! rtph264pay config-interval=1 pt=96 \
# ! gdppay \
# ! gdpdepay \
# ! rtph264depay \
# ! avdec_h264 \
# ! autovideosink sync=false
# # ! tcpserversink host=192.168.0.101 port=5000 \


