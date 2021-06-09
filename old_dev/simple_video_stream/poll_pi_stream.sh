#!/bin/bash
NUM_RETRIES=10
PI_ADDR=192.168.0.107

success=1
i="0"
while [[ ($i -lt $NUM_RETRIES) && ($success -eq 1) ]]; do
  echo "Attempt $i to connect to pi stream"
  # Check if the port is open
  nc -nzvw10 $PI_ADDR 5000
  success=$?
  if [ $success -eq 0 ]; then
    echo "Connection successful"
    gst-launch-1.0 tcpclientsrc host=$PI_ADDR port=5000 \
    ! matroskademux \
    ! decodebin \
    ! videoconvert \
    ! autovideosink sync=false
  else
    sleep 5
  fi
  i=$[$i+1]
done
