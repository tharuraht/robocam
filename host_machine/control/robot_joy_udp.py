#!/usr/bin/env python3
# Enables the joystick to be attached to one computer while a different computer
# connected to the same LAN communicates with the car by BLE. The connection
# between the two uses UDP.
# Based on work from Dr. Adria Junyent-Ferre
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv
import time
import pygame
import socket
import json
from collections import defaultdict


def joystick_init():
    pygame.init()
    pygame.joystick.init()

    try:
        j = pygame.joystick.Joystick(0)
        j.init()
    except Exception as e:
        print("Error initialising joystick:", e)
        exit(1)
    return j

def send_map(joymap, conf):
    port = conf['pi']['control_port']
    addr = conf['pi']['vpn_addr']

    dump = json.dumps(joymap)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(dump.encode(),(addr, port))
    

def control_loop(j, conf):

    prevmap = defaultdict(bool)
    try:
        while True:
            joymap = defaultdict(bool)
            pygame.event.pump()

            # Get joystick values
            joymap['x'] = j.get_axis(0)*99
            joymap['y'] = -j.get_axis(1)*99

            for i in range(j.get_numbuttons()):
                joymap[f"b_{i}"] = j.get_button(i)
            
            
            hat = j.get_hat(0)
            joymap["h_up"] = (hat[1] == 1)
            joymap["h_right"] = (hat[0] == 1)
            joymap["h_down"] = (hat[1] == -1)
            joymap["h_left"] = (hat[0] == -1)

            # print(joymap)
            if(joymap != prevmap):
                # print (joymap)
                send_map(joymap, conf)
                pass
            else:
                # print ("stndby: "+miss)
                pass 
            time.sleep(0.05)
            prevmap = joymap.copy()
    except KeyboardInterrupt:
        joymap = defaultdict(bool)
        joymap['x'] = 0
        joymap['y'] = 0
        send_map(joymap, conf)
        time.sleep(1)


def main():
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)

    j = joystick_init()

    control_loop(j, conf)


if __name__ == "__main__":
    main()