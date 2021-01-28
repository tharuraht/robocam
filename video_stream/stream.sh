gst-launch-1.0 rpicamsrc rotation=180 preview=false bitrate=1000000 \
    ! 'video/x-h264,width=640,height=480' \
    ! h264parse \
    ! queue \
    ! rtph264pay config-interval=1 pt=96 \
    ! gdppay \
    ! udpsink host=192.168.0.99 port=5000
