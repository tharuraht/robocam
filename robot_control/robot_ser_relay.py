#!/usr/bin/env python3
# Relay program, waits for incoming commands from host machine and forwards to
# the nrf80001/robot plaftform
# Based on work from Dr. Adria Junyent-Ferré
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv

import time
import socket
import argparse
import serial

DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 5005

parser = argparse.ArgumentParser(description="Receives control signals created by\
    host machine and relays to robot platform")
parser.add_argument('SERIAL_PORT', type=str)
parser.add_argument('--sourceIP', type=str, default=DEFAULT_UDP_IP,
    help='IP address of this device')
parser.add_argument('--port', type=str, default=DEFAULT_UDP_PORT,
    help='Port to listen on')

args = parser.parse_args()
UDP_IP = args.sourceIP
UDP_PORT = args.port
SER_PORT = args.SERIAL_PORT

try:
    #Connect to Arduino serial port
    ser = serial.Serial(SER_PORT, 9800, timeout=1)
except Exception as e:
    print(e)
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
        pass
except KeyboardInterrupt:
  ser.close()
  time.sleep(1)
