#SERVER=4grobo.zapto.org
SERVER=10.200.200.1

gst-launch-1.0 rpicamsrc annotation-mode=time preview=false vflip=true bitrate=100000 keyframe-interval=-1 ! \
	video/x-h264, framerate=25/1, height=720, width=1280 ! h264parse ! \
	rtspclientsink debug=true protocls=udp-mcast+udp location=rtsp://$SERVER:5000/test latency=0 ulpfec-percentage=10

