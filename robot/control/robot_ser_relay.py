#!/usr/bin/env python3
# Relay program, waits for incoming commands from host machine and forwards to
# robot plaftform via USB serial connection
# Based on work from Dr. Adria Junyent-Ferré
# https://hackaday.io/project/170624-wi-fi-controlled-car-turtle-bot-with-fpv

import time
import socket
import serial
import os
from pathlib import Path
import json
import logging
import select
import subprocess


class Serial_Relay():
    device_found = False
    dev_port = 0
    udp_port = 0
    conf = None
    ser = None

    def __init__(self, conf):
        self.conf = conf
        # Configure Logger
        logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
        level=logging.getLevelName(conf['log_level']))
        
        # Check for arduino port
        self.find_device()
        if self.device_found:
            self.ser = connect_serial()
            print(f"Arduino connected at port {self.dev_port}")
        

        self.udp_port = self.conf['pi']['control_port']
    
    def __del__(self):
        if self.ser is not None:
            self.ser.close()
            time.sleep(1)
    

    def find_device(self):
        p=subprocess.run(["ls", "/dev/ttyUSB*"], shell=False, stdout=subprocess.PIPE, universal_newlines=True)
        if p.returncode == 0:
            self.device_found = True
            print(p.stdout)
            self.dev_port = p.stdout

    def connect_serial(self):
        try:
            #Connect to Arduino serial port
            logging.debug(f"Connecting to serial port {self.dev_port}")
            ser = serial.Serial(self.dev_port, 9800, timeout=1)
        except Exception as e:
            logging.exception(e)
            upnp.close_port()
            exit(1)
        return ser


    def write_dev(self, msg):
        """
        Write to serial port of arduino. Functions only if arduino serial port
        was discovered and connected.
        """
        if self.device_found:
            logging.debug(f"Writing {msg} to serial port...")
            self.ser.write(msg)


    def run(self):
        """
        Self contained loop to receive movement commands from udp port and write
        to serial port.
        """

        time.sleep(1)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0) # Make socket non-blocking
        sock.bind(("",self.udp_port))
        logging.info(f"Ready to receive at port {self.udp_port}")

        timeout = 1 #1 s
        misp="x,x"
        while True:
            ready = select.select([sock], [], [], timeout)
            if ready[0]:

                miss, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
                # logging.debug(f"received message: {miss}")
                if miss!=misp:
                    self.write_dev(miss)
                    misp=miss
                else:
                    # print ("stndby: ",miss)
                    pass
            else:
                self.write_dev((0,0))




if __name__ == "__main__":
    # Fetch config
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    with open(os.path.join(source_dir,'..','..','robocam_conf.json')) as f:
        conf = json.load(f)

    s = Serial_Relay(conf)
    s.run()