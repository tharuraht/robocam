#!/usr/bin/env python3
# Relay program, waits for incoming commands from host machine and forwards to
# the nrf80001/robot plaftform
# Based on work from Dr. Adria Junyent-Ferré
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv

# Note: bluepy only works on Linux
from bluepy import btle
import time
import socket
import argparse

DEFAULT_UDP_IP = "0.0.0.0"
DEFAULT_UDP_PORT = 5005
BLE_MAC_ADDR = "E1:E4:71:C4:5C:7B"

parser = argparse.ArgumentParser(description="Receives control signals created by\
    host machine and relays to robot platform")
parser.add_argument('--sourceIP', type=str, default=DEFAULT_UDP_IP,
    help='IP address of this device')
parser.add_argument('--port', type=str, default=DEFAULT_UDP_PORT,
    help='Port to listen on')

args = parser.parse_args()
UDP_IP = args.targetIP
UDP_PORT = args.targetPort

try:
  dev = btle.Peripheral(BLE_MAC_ADDR, btle.ADDR_TYPE_RANDOM)
except Exception as e:
  print(e)
  exit(1)

time.sleep(1)
print("services: ", dev.getServices())

serv=dev.getServiceByUUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
characteristics=serv.getCharacteristics()
han=characteristics[0].getHandle()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

misp="x,x"
try:
  while True:
    miss, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print ("received message: ",miss)
    if miss!=misp:
          dev.writeCharacteristic(han,miss)
          misp=miss
    else:
          print ("stndby: ",miss)
except KeyboardInterrupt:
  dev.writeCharacteristic(han,"0,0")
  time.sleep(1)

  dev.disconnect()
