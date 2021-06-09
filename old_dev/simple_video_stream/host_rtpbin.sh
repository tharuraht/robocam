PI_IP="10.200.200.2"

gst-launch-1.0 -v rtpbin name=rtpbin drop-on-latency=TRUE  latency=200 \
do-retransmission=TRUE autoremove=TRUE fec-decoders='fec,0="rtpst2022-1-fecdec\ size-time\=1000000000";' \
udpsrc port=5002 caps="application/x-rtp, payload=96" ! queue ! rtpbin.recv_fec_sink_0_0 \
udpsrc port=5003 caps="application/x-rtp, payload=96" ! queue ! rtpbin.recv_fec_sink_0_1 \
udpsrc port=5000 caps="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=102" \
! queue ! rtpbin.recv_rtp_sink_0 \
rtpbin. ! rtph264depay ! avdec_h264 ! queue ! autovideosink   sync=false                 \
udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
rtpbin.send_rtcp_src_0 ! udpsink host=$PI_IP port=5004 sync=false async=false

# udpsrc caps="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264" \
# port=5000 ! queue ! rtpbin.recv_rtp_sink_0                                \
# rtpbin. ! rtph264depay ! avdec_h264 ! autovideosink  