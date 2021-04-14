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

utils_path = os.path.join(os.getcwd(),'..','..','utils')
sys.path.insert(1, utils_path)
import upnp_setup

DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 5005

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
    print(f"Connecting to serial port {SER_PORT}")
    ser = serial.Serial(SER_PORT, 9800, timeout=1)
except Exception as e:
    print(e)
    upnp.close_port()
    exit(1)

time.sleep(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

misp="x,x"
try:
  while True:
    miss, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print ("received message: ",miss)
    if miss!=misp:
        ser.write(miss)
        misp=miss
    else:
        # print ("stndby: ",miss)
        # pass
        ser.write(0,0)
except KeyboardInterrupt:
  ser.close()
  time.sleep(1)

upnp.close_port()