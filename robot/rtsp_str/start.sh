#!/usr/bin/env bash

python3 stat_rec.py &
P1=$!
python3 rtsp_stream.py &
P2=$!
wait $P1 $P2