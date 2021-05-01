#!/usr/bin/python3
# Stat receiver, listens for sent stats and updates stat file
import socket
import json
import logging

with open("robocam_conf.json") as conf_file:
    conf = json.load(conf_file)

# Configure Logger
logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
    level=logging.getLevelName(conf['log_level']))

port = conf['pi']['comms_port']

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', port))
logging.info(f"Listening for RTCP Stats on port {port}")

while True:
    data, addr = sock.recvfrom(1024)
    data = data.decode('utf-8')
    #TODO avoid spam
    #print("received message: %s" % data)
    with open("rec_stats.tmp","w") as f:
        f.write(data)
