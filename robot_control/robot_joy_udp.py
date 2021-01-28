#!/usr/bin/env python
# Enables the joystick to be attached to one computer while a different computer
# connected to the same LAN communicates with the car by BLE. The connection
# between the two uses UDP.
# Based on work from Dr. Adria Junyent-Ferré
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv
import time
import pygame
import socket
import argparse

DEFAULT_UDP_PORT = 5005

# Define arguments
parser = argparse.ArgumentParser(description="Sends control signals created by\
    video game controller")
parser.add_argument('targetIP', type=str, help='IP address of target device')
parser.add_argument('--targetPort', type=str, default=DEFAULT_UDP_PORT,
    help='Target port to send to')

args = parser.parse_args()
UDP_IP = args.targetIP
UDP_PORT = args.targetPort

pygame.init()
pygame.joystick.init()

try:
    j = pygame.joystick.Joystick(0)
    j.init()
except Exception as e:
    print("Error initialising joystick:", e)
    exit(1)

print ("UDP target IP:", UDP_IP)
print ("UDP target port:", UDP_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

miss="99,99"
try:
    while True:
        pygame.event.pump()
        x=j.get_axis(0)*99
        y=-j.get_axis(1)*99
        misp=miss
        miss="{:.0f}".format(x)+","+"{:.0f}".format(y)
        if(miss!=misp):
            print (miss)
            sock.sendto(miss.encode(),(UDP_IP, UDP_PORT))
        else:
            # print ("stndby: "+miss)
            pass
        time.sleep(0.05)
except KeyboardInterrupt:
    sock.sendto("0,0",(UDP_IP, UDP_PORT))
    time.sleep(1)
