#!/usr/bin/env python

from bluepy import btle
import time
import socket

try:
  dev = btle.Peripheral("E1:E4:71:C4:5C:7B", btle.ADDR_TYPE_RANDOM) # replace the MAC address by yours
except Exception as e:
  print(e)

time.sleep(1)
print("services: ", dev.getServices())

serv=dev.getServiceByUUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
characteristics=serv.getCharacteristics()
han=characteristics[0].getHandle()

UDP_IP = "192.168.0.77"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
sock.bind((UDP_IP, UDP_PORT))

misp="x,x"
while True:
   miss, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
   print "received message: "+miss
   if miss!=misp:
        dev.writeCharacteristic(han,miss)
        misp=miss 
   else:
        print "stndby: "+miss

dev.writeCharacteristic(han,"0,0") 
time.sleep(1)

dev.disconnect() 
