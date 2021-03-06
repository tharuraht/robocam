#!/usr/bin/env python3
import socket
import json
from collections import defaultdict
from pathlib import Path
from control import robot_ser_relay
import os
import logging


class Central_Control():
    relay = None
    sock = None
    streamer_q = None # Queue to send data to streamer
    rewind_mode = False

    def __init__(self, conf, ctrl_streamer_q = None):
        self.conf = conf
        self.relay = robot_ser_relay.Serial_Relay(conf)
        self.setup_socket()
        self.streamer_q = ctrl_streamer_q

        logging.basicConfig(filename=conf['log_path'], filemode='a',
        format=conf['log_format'], level=logging.getLevelName(conf['log_level']))


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
        self.sock.settimeout(0.01)

        logging.info(f"Ready to receive at {UDP_IP}:{UDP_PORT}")


    def parse_map(self, joymap):
        comm = self.conf["controller_config"]

        if {"x", "y"} <= joymap.keys():
            self.rewind_mode = False
            # Movement controls, send to relay
            self.relay.write_dev("{:.0f},{:.0f}".format(joymap['x'],joymap['y']))
            # Save to history as tuple
            self.relay.save_history(joymap['x'],joymap['y'])

        if joymap[comm["REWIND"]]:
            logging.info("Rewinding")
            self.rewind_mode = True
            self.relay.rewind()
        elif not joymap[comm["REWIND"]]:
            self.rewind_mode = False

        if self.streamer_q is not None:
            try:
                if joymap[comm["RESTART_PI"]]:
                    logging.info("Restarting Pi")
                    os.system("sudo reboot")
                if joymap[comm["RESTART_STREAM"]]:
                    logging.info("Restarting Streamer Pipeline")
                    self.streamer_q.put("[PIPE_RESTART]")
                if joymap[comm["TOGGLE_LOW_BITRATE"]]:
                    logging.info("Toggling low-bitrate mode")
                    self.streamer_q.put("[TOGGLE_LOW_BITRATE]")

                # Control FPS
                if joymap[comm["INC_FPS"]]:
                    logging.info("Increasing FPS")
                    self.streamer_q.put("[INC_FPS]")
                elif joymap[comm["DEC_FPS"]]:
                    logging.info("Decreasing FPS")
                    self.streamer_q.put("[DEC_FPS]")

                # Control Bitrate
                if joymap[comm["INC_RATE"]]:
                    logging.info("Increasing Bitrate")
                    self.streamer_q.put("[INC_RATE]")
                elif joymap[comm["DEC_RATE"]]:
                    logging.info("Decreasing Bitrate")
                    self.streamer_q.put("[DEC_RATE]")

                # Toggle stats
                if joymap[comm["TOGGLE_STATS"]]:
                    logging.info("Toggling stats...")
                    self.streamer_q.put("[TOGGLE_STATS]")
                if joymap[comm["TOGGLE_SEC_CAM"]]:
                    logging.info("Toggling second camera...")
                    self.streamer_q.put("[TOGGLE_SEC_CAM]")
            except KeyError:
                pass
        else:
            logging.warning("Streamer control queue not set")


    def control_loop(self):
        prevmap = defaultdict(bool)
        while True:
            try:
                data = self.sock.recv(1024) # buffer size is 1024 bytes TODO check if big enough
                # logging.debug("Data received: %s" % data)
                joymap = json.loads(data.decode())

                if joymap != prevmap:
                    logging.debug(joymap)
                    self.parse_map(joymap)
            except socket.timeout:
                if self.rewind_mode == True:
                    self.relay.rewind()


if __name__ == "__main__":
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    with open(os.path.join(source_dir,'..','..','robocam_conf.json')) as f:
        conf = json.load(f)
    ctrl = Central_Control(conf)
    ctrl.control_loop()