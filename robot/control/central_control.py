#!/usr/bin/env python3
import socket
import time
import json
from collections import defaultdict
from pathlib import Path
from control import robot_ser_relay
import os


class Central_Control():
    relay = None
    sock = None
    streamer_q = None # Queue to send data to streamer

    def __init__(self, conf, ctrl_streamer_q = None):
        self.conf = conf
        self.relay = robot_ser_relay.Serial_Relay(conf)
        self.setup_socket()
        self.streamer_q = ctrl_streamer_q
    
    def  __del__(self):
        if self.sock is not None:
            self.sock.close()

    def setup_socket(self):
        # Setup receiver socket
        UDP_IP = ""
        UDP_PORT = self.conf['pi']['control_port']
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.setblocking(0) # Make socket non-blocking
        self.sock.bind((UDP_IP, UDP_PORT))

        print(f"Ready to receive at {UDP_IP}:{UDP_PORT}")

    def parse_map(self, joymap):
        comm = self.conf["controller_config"]
        if {"x", "y"} <= joymap.keys():
            # Movement controls, send to relay
            self.relay.write_dev("{:.0f},{:.0f}".format(joymap['x'],joymap['y']))

        if self.streamer_q is not None:
            if joymap[comm["RESTART_PI"]]:
                print("Restarting Pi")
                # TODO shutdown all and restart pi
            
            if joymap[comm["RESTART_STREAM"]]:
                self.streamer_q.put("[PIPE_RESTART]")

            if joymap[comm["INC_FPS"]]:
                print("Increasing FPS")
                self.streamer_q.put("[INC_FPS]")
            elif joymap[comm["DEC_FPS"]]:
                print("Decreasing FPS")
                self.streamer_q.put("[DEC_FPS]")

            # Toggle stats
            if joymap[comm["TOGGLE_STATS"]]:
                print("Toggling stats...")
                self.streamer_q.put("[TOGGLE_STATS]")
            if joymap[comm["TOGGLE_SEC_CAM"]]:
                print("Toggling second camera...")
                self.streamer_q.put("[TOGGLE_SEC_CAM]")
        else:
            print("Streamer control queue not set")


    def control_loop(self):
        prevmap = defaultdict(bool)
        while True:
            data = self.sock.recv(1024) # buffer size is 1024 bytes TODO check if big enough
            # print("Data received: %s" % data)

            joymap = json.loads(data.decode())

            if joymap != prevmap:
                print(joymap)
                self.parse_map(joymap)

if __name__ == "__main__":
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    with open(os.path.join(source_dir,'..','..','robocam_conf.json')) as f:
        conf = json.load(f)
    ctrl = Central_Control(conf)
    ctrl.control_loop()