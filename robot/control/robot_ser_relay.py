#!/usr/bin/env python3
# Relay program, waits for incoming commands from host machine and forwards to
# robot plaftform via USB serial connection
# Based on work from Dr. Adria Junyent-Ferré
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv

import time
import socket
import argparse
import serial
import os
import sys
from pathlib import Path
import json
import logging
import select

# Import upnp_setup
source_path = Path(__file__).resolve()
source_dir = source_path.parent
utils_path = os.path.join(source_dir,'..','..','utils')
sys.path.insert(1, utils_path)
import upnp_setup

# Fetch config
with open(os.path.join(source_dir,'..','..','robocam_conf.json')) as f:
    conf = json.load(f)

# Configure Logger
logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
    level=logging.getLevelName(conf['log_level']))

DEFAULT_UDP_IP = ""
DEFAULT_UDP_PORT = conf['pi']['control_port']

parser = argparse.ArgumentParser(description="Receives control signals created by\
    host machine and relays to robot platform")
parser.add_argument('SERIAL_PORT', type=str)
parser.add_argument('--sourceIP', type=str, default=DEFAULT_UDP_IP,
    help='IP address of this device')
parser.add_argument('--port', type=str, default=DEFAULT_UDP_PORT,
    help='Port to listen on')
parser.add_argument('--port_forward', action='store_true')

args = parser.parse_args()
UDP_IP = args.sourceIP
UDP_PORT = args.port
SER_PORT = args.SERIAL_PORT

if args.port_forward:
    #Open UPnP port
    lan = None
    # lan = '192.168.8.107'
    upnp = upnp_setup.upnp_port(UDP_PORT, mode='UDP', lanoverride = lan) 

try:
    #Connect to Arduino serial port
    logging.debug(f"Connecting to serial port {SER_PORT}")
    ser = serial.Serial(SER_PORT, 9800, timeout=1)
except Exception as e:
    logging.exception(e)
    upnp.close_port()
    exit(1)

time.sleep(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(0) # Make socket non-blocking
sock.bind((UDP_IP, UDP_PORT))
logging.info(f"Ready to receive at {UDP_IP}:{UDP_PORT}")

timeout = 1 #500 ms

misp="x,x"
try:
  while True:
    ready = select.select([sock], [], [], timeout)
    if ready[0]:

        miss, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        logging.debug(f"received message: {miss}")
        if miss!=misp:
            ser.write(miss)
            misp=miss
        else:
            # print ("stndby: ",miss)
            pass
    else:
        ser.write((0,0))
except KeyboardInterrupt:
  ser.close()
  time.sleep(1)
finally:
    if args.port_forward:
        upnp.close_port()
