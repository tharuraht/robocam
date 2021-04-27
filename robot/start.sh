#!/usr/bin/env bash
GST_PATH=$(python3 $ROBOCAM_DIR/utils/parse_json.py "pi" "gst_path" -j robocam_conf.json)
RTSP_PATH=$ROBOCAM_DIR/robot/rtsp_str/

echo $GST_PATH

trap "rm -f rec_stats.tmp; exit" INT TERM ERR
trap "kill 0" EXIT

python3 $RTSP_PATH/stat_rec.py &                #RTCP Stat Receiver
$GST_PATH python3 $RTSP_PATH/rtsp_stream.py &   #RTSP Server
$ROBOCAM_DIR/robot/control/start_relay.sh &     #Robot control relay

wait


# (trap 'kill 0' SIGINT; python3 $RTSP_PATH/stat_rec.py & $GST_PATH python3 $RTSP_PATH/rtsp_stream.py)