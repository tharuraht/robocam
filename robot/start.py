#!/usr/bin/env python3
# https://stackoverflow.com/questions/43861164/passing-data-between-separately-running-python-scripts
from multiprocessing import Process, Queue
from control import central_control
from rtsp_str import rtsp_stream
import json
import os

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path,'..','robocam_conf.json')) as f:
        conf = json.load(f)

    ctrl_streamer_q = Queue() # Queue from ctrl to streamer
    ctrl = central_control.Central_Control(conf, ctrl_streamer_q)
    streamer = rtsp_stream.video_streamer(conf, ctrl_streamer_q)

    ctrl_p = Process(target=ctrl.control_loop)
    ctrl_p.daemon = True
    ctrl_p.start()

    streamer.launch()

if __name__ == "__main__":
    main()