BITRATE=1000000
HOSTIP=10.200.200.1

gst-launch-1.0 -v rtpbin name=rtpbin fec-encoders='fec,0="rtpst2022-1-fecenc\ rows\=3\ columns\=3";' \
rpicamsrc preview=false vflip=true annotation-mode=time+date+custom-text name=src \
bitrate=$BITRATE annotation-text=\"Bitrate $BITRATE \" \
! video/x-h264,framerate=15/1,width=1280,height=720,profile=high,payload=33 \
! h264parse \
! rtph264pay ssrc=0 pt=102 \
! rtpbin.send_rtp_sink_0 \
rtpbin.send_rtp_src_0 ! queue ! udpsink port=5000 host=$HOSTIP                         \
rtpbin.send_rtcp_src_0 ! queue ! udpsink port=5001 host=$HOSTIP sync=false async=false    \
rtpbin.send_fec_src_0_0 ! udpsink host=$HOSTIP port=5002 async=false \
rtpbin.send_fec_src_0_1 ! udpsink host=$HOSTIP port=5003 async=false \
udpsrc port=5004 ! rtpbin.recv_rtcp_sink_0