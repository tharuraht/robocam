export GST_PLUGIN_PATH="/home/pi/Documents/latency-clock"
GST_PATH=/home/pi/Downloads/gst-build/gst-env.py
export GST_DEBUG=timestampoverlay:5

$GST_PATH gst-launch-1.0 rpicamsrc preview=false rotation=180 annotation-mode=time+date name=videosrc bitrate=2000000 \
! video/x-raw,framerate=25/1,width=1600,height=900 \
! timestampoverlay \
! omxh264enc \
! video/x-h264 \
! queue \
! rtph264pay \
! gdppay \
! udpsink host=10.200.200.1 port=5000
# ! tcpserversink host=10.200.200.2 port=5000