#!/usr/bin/env python3
# https://stackoverflow.com/questions/43861164/passing-data-between-separately-running-python-scripts
from multiprocessing import Process, Queue
from control import robot_control
from rtsp_rec import rtsp_server, upnp_rtsp, ps_bitrate
import json
import os
import time
import subprocess
import shutil
import logging

def open_upnp():
    prev_res = ""
    while True:
        time.sleep(1)
        res = subprocess.run("lsof -i4 -n | grep python | grep UDP", shell=True, stdout=subprocess.PIPE)
        # print(res.returncode, res.stdout)
        if res.returncode == 0:
            out = res.stdout.decode('utf-8')
            if res.stdout != prev_res:
                upnp_rtsp.open_new_ports(out)
                prev_res = res.stdout

def cleanup(conf):
    print("Cleanup")
    if conf["host"]["open_upnp"]:
        upnp_rtsp.close_ports()
    shutil.rmtree('tmp')


def main():
    if os.path.exists('tmp'):
        shutil.rmtree('tmp')
    os.mkdir('tmp')


    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path,'..','robocam_conf.json')) as f:
        conf = json.load(f)

    open(conf['log_path'], 'w').close() # Clear log file
    logging.basicConfig(filename=conf['log_path'], filemode='a',
    format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Starting robocam system on Host Machine...")
    logging.info("Log directory: %s" % conf['log_path'])

    ctrl_rec_q = Queue() # Queue from ctrl to rec

    try:
        rec = rtsp_server.RTSP_Server(conf,ctrl_rec_q)
        ps = ps_bitrate.PS_Bitrate(conf)

        ctrl_p = Process(target=robot_control.control_loop, daemon=True, args=(conf,ctrl_rec_q,))
        ctrl_p.start()

        rec_p = Process(target=rec.launch)
        rec_p.start()

        ps_p = Process(target=ps.start, daemon=True)
        ps_p.start()

        if conf["host"]["open_upnp"]:
            print("Upnp port opener active")
            upnp_p = Process(target=open_upnp, daemon=True)
            upnp_p.start()


        while True:
            time.sleep(5)
            if not rec_p.is_alive():
                rec_p = Process(target=rec.launch)
                rec_p.start()

        ctrl_p.join()
    except KeyboardInterrupt:
        cleanup(conf)
    except Exception as e:
        print(e)
        cleanup(conf)



if __name__ == "__main__":
    main()