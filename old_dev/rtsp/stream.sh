/home/pi/Downloads/gst-rtsp-server-1.14.2/examples/test-launch "( rpicamsrc preview=false vflip=true bitrate=300000 keyframe-interval=-1 ! video/x-h264, framerate=15/1, width=1280, height=720 ! h264parse ! rtph264pay name=pay0 pt=96 )"