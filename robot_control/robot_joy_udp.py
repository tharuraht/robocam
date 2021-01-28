#!/usr/bin/env python

import time
import pygame
#import math
import socket

pygame.init()
pygame.joystick.init()
j = pygame.joystick.Joystick(0)
j.init()

UDP_IP = "192.168.0.101"
UDP_PORT = 5005
print ("UDP target IP:", UDP_IP)
print ("UDP target port:", UDP_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

miss="99,99"
while True:
    pygame.event.pump()
    x=j.get_axis(0)*99
    y=-j.get_axis(1)*99
    misp=miss
    miss="{:.0f}".format(x)+","+"{:.0f}".format(y)
    if(miss!=misp):
        print (miss)
        sock.sendto(miss,(UDP_IP, UDP_PORT))
    else:
        print ("stndby: ",miss)
    time.sleep(0.05)

sock.sendto("0,0",(UDP_IP, UDP_PORT))
time.sleep(1)

dev.disconnect() 
