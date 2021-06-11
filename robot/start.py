#!/usr/bin/env python3
# https://stackoverflow.com/questions/43861164/passing-data-between-separately-running-python-scripts
from multiprocessing import Process, Queue
from control import central_control, pi_stats
from rtsp_str import rtsp_stream
import json
import os
import time
import logging

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path,'..','robocam_conf.json')) as f:
        conf = json.load(f)

    
    open(conf['log_path'], 'w').close() # Clear log file
    logging.basicConfig(filename=conf['log_path'], filemode='a',
    format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Starting robocam system on RPi...")
    logging.info("Log directory: %s" % conf['log_path'])

    ctrl_streamer_q = Queue() # Queue from ctrl to streamer
    ctrl = central_control.Central_Control(conf, ctrl_streamer_q)
    streamer = rtsp_stream.video_streamer(conf, ctrl_streamer_q)
    stats = pi_stats.Pi_Stats(conf)

    ctrl_p = Process(target=ctrl.control_loop, daemon=True)
    streamer_p = Process(target=streamer.launch)
    stats_p = Process(target=stats.main_loop)
    try:
        ctrl_p.start()
        streamer_p.start()
        stats_p.start()

        while True:
            time.sleep(5)
            if not streamer_p.is_alive():
                logging.info("Restarting Streamer after error...")
                streamer_p = Process(target=streamer.launch)
                streamer_p.start()
            
            if not ctrl_p.is_alive():
                logging.info("Restarting Central Control after error...")
                ctrl_p = Process(target=ctrl.control_loop, daemon=True)
                ctrl_p.start()
            
            if not stats_p.is_alive():
                logging.info("Restarting Pi Stats after error...")
                stats_p = Process(target=stats.main_loop)
                stats_p.start()


        # ctrl_p.join()
    finally:
        print("Cleanup")
        for proc in [ctrl_p, streamer_p, stats_p]:
            if proc.is_alive():
                proc.terminate()
    

if __name__ == "__main__":
    main()