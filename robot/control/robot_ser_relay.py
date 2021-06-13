#!/usr/bin/env python3
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
    """
    Connects to Arduino and relays movement commands
    """
    device_found = False
    conf = None
    ser = None

    # Rewind variables
    prev_time = 0
    prev_move = (0,0)
    movement_history = []
    max_history = 1000

    def __init__(self, conf):
        self.conf = conf
        # Configure Logger
        # logging.basicConfig(filename=conf['log_path'], filemode='a',
        # format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
        # logging.getLogger().addHandler(logging.StreamHandler())

        self.setup_device()


    def __del__(self):
        if self.ser is not None:
            self.ser.close()
            time.sleep(1)


    def setup_device(self):
        # Find Arduino
        dev_port = self.conf['pi']['arduino_port']

        #Connect to Arduino serial port
        try:
            logging.debug(f"Connecting to serial port {dev_port}")
            self.ser = serial.Serial(dev_port, 9800, timeout=1)
            self.device_found = True
        except Exception as e:
            logging.exception(e)
            exit(1)
        logging.info(f"Arduino connected at port {dev_port}")


    def write_dev(self, msg):
        """
        Write to serial port of arduino. Functions only if arduino serial port
        was discovered and connected.
        """
        if self.device_found:
            logging.debug(f"Writing {msg} to serial port...")
            self.ser.write(msg.encode('utf-8'))

    def rewind(self):
        """
        Uses movement history to sent previous commands
        """
        logging.debug(len(self.movement_history))
        if len(self.movement_history) > 0:
            x, y, duration = self.movement_history.pop()
            logging.debug("Rewinding...",x,y,duration)
            self.write_dev("{:.0f},{:.0f}".format(-x,-y))
            time.sleep(duration)
        else:
            self.write_dev("{:.0f},{:.0f}".format(0,0))


    def save_history(self,x,y):
        cur_time = time.time()
        if (abs(x)+abs(y) > 1) or \
            (abs(self.prev_move[0]) + abs(self.prev_move[1]) > 1):

            if self.prev_time == 0:
                self.prev_time = cur_time

            duration = cur_time - self.prev_time
            logging.debug("DURATION: %0d" % duration)

            if len(self.movement_history) >= self.max_history:
                    self.movement_history.pop(0)
            self.movement_history.append((x, y, duration))
            self.prev_time = cur_time
            self.prev_move = (x,y)
        else:
            self.prev_time = 0


    def run(self):
        """
        Self contained loop to receive movement commands from udp port and write
        to serial port.
        """

        # time.sleep(1)
        udp_port = self.conf['pi']['control_port']

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0) # Make socket non-blocking
        sock.bind(("",udp_port))
        logging.info(f"Ready to receive at port {udp_port}")

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


class BLE_Relay(Serial_Relay):
    """
    Derived from Serial_Relay to use BLE connection to robot
    """
    ble_mac_addr = "E1:E4:71:C4:5C:7B" # Set this to your BLE module mac addr
    handle = None

    def __init__(self,conf):
        bluepy = __import__('bluepy') # only import if class used
        super().__init__(conf)

    def __del__(self):
        if self.ser is not None:
            self.ser.disconnect()
            time.sleep(1)


    def setup_device(self):
        try:
            dev = self.bluepy.btle.Peripheral(self.ble_mac_addr, self.bluepy.btle.ADDR_TYPE_RANDOM)
        except Exception as e:
            logging.exception(e)
            exit(1)

        self.device_found = True
        time.sleep(1)
        logging.debug("services: ", dev.getServices())
        serv=dev.getServiceByUUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
        characteristics=serv.getCharacteristics()

        self.handle=characteristics[0].getHandle()
        self.ser = dev
        logging.info("BLE device connected")


    def write_dev(self, msg):
        """
        Write to serial port of arduino. Functions only if arduino serial port
        was discovered and connected.
        """
        if self.device_found:
            logging.debug(f"Writing {msg} to BLE port...")
            self.ser.writeCharacteristic(self.handle, msg.encode('utf-8'))


if __name__ == "__main__":
    # Fetch config
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    with open(os.path.join(source_dir,'..','..','robocam_conf.json')) as f:
        conf = json.load(f)

    s = Serial_Relay(conf)
    s.run()