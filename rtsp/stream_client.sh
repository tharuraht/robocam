SERVER=4grobo.zapto.org
#SERVER=10.200.200.1

gst-launch-1.0 rpicamsrc preview=false vflip=true bitrate=100000 keyframe-interval=-1 ! video/x-h264, framerate=25/1, height=720, width=1280 ! h264parse ! rtspclientsink debug=true port-range=5001 location=rtsp://$SERVER:5000/test latency=0 ulpfec-percentage=5

