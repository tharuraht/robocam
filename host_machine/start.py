#!/usr/bin/env python3
# Host machine process manager
from multiprocessing import Process, Queue
from control import robot_control, sys_stats
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

def upnp_cleanup(conf):
    print("Cleanup")
    if conf["host"]["open_upnp"]:
        upnp_rtsp.close_ports()
    shutil.rmtree('tmp')


def logging_setup(conf):
    open(conf['log_path'], 'w').close() # Clear log file
    logging.basicConfig(filename=conf['log_path'], filemode='a',
    format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Starting robocam system on Host Machine...")
    logging.info("Log directory: %s" % conf['log_path'])

def main():
    if os.path.exists('tmp'):
        shutil.rmtree('tmp')
    os.mkdir('tmp')

    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path,'..','robocam_conf.json')) as f:
        conf = json.load(f)

    logging_setup(conf)

    # Create queues to pass data between processes
    ctrl_rec_q = Queue() # Queue from ctrl to rec

    # Process classes, pass queue to constructors
    rec = rtsp_server.RTSP_Server(conf,ctrl_rec_q)
    ps = ps_bitrate.PS_Bitrate(conf)
    stats = sys_stats.Sys_Stats(conf)


    # Initalise processes
    ctrl_p = Process(target=robot_control.control_loop, daemon=True, args=(conf,ctrl_rec_q,))
    rec_p = Process(target=rec.launch)
    ps_p = Process(target=ps.start, daemon=True)
    stats_p = Process(target=stats.event_loop, daemon=True)

    proc_lst = [ctrl_p, rec_p, stats_p, ps_p]

    # Only start upnp if needed
    if conf["host"]["open_upnp"]:
        logging.info("Upnp port opener active")
        upnp_p = Process(target=open_upnp, daemon=True)
        proc_lst.append(upnp_p)


    try:
        for proc in proc_lst:
            proc.start()

        while True:
            time.sleep(5)
            if not rec_p.is_alive():
                rec_p = Process(target=rec.launch)
                rec_p.start()

            if not ctrl_p.is_alive():
                ctrl_p = Process(target=robot_control.control_loop, daemon=True, args=(conf,ctrl_rec_q,))
                ctrl_p.start()

            if not ps_p.is_alive():
                ps_p = Process(target=ps.start, daemon=True)
                ps_p.start()

            if not stats_p.is_alive():
                stats_p = Process(target=stats.event_loop, daemon=True)
                stats_p.start()
    except Exception as e:
        print(e)
    finally:
        print("Cleanup")
        upnp_cleanup(conf)
        for proc in proc_lst:
            if proc.is_alive():
                proc.terminate()



if __name__ == "__main__":
    main()