gst-launch-1.0 rpicamsrc preview=false rotation=180 annotation-mode=time+date name=videosrc bitrate=2000000 \
! h264parse \
! video/x-h264,framerate=25/1,width=1280,height=720 \
! matroskamux \
! tcpserversink host=192.168.0.77 port=5000