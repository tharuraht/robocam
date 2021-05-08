#!/usr/bin/python3
from subprocess import Popen, PIPE
import os
from select import select
import sys
from multiprocessing import Process, Queue
from control import Central_Control

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)

stat_rec_path = os.path.join(dir_path,'rtsp_str','stat_rec.py')
rtsp_str_path = os.path.join(dir_path,'rtsp_str','rtsp_stream.py')
ctrl_relay_path = os.path.join(dir_path,'control','robot_ser_relay.py')

# proc_lst = [stat_rec_p, rtsp_str_p]

# Popen keyword arguments and defaults
kwds = {
    "stdout": PIPE,
    "bufsize": 1,
    "close_fds": True,
    "universal_newlines": True,
}

path_lst = [stat_rec_path, rtsp_str_path]
proc_lst = [Popen(cmd, **kwds) for cmd in path_lst]

def safe_termination(procs):
    print('Safe exit')
    # Cleanup
    if os.path.exists('rec_stats.tmp'):
        os.remove('rec_stats.tmp')

    # Terminate remaining processes
    for proc in procs:
        proc.terminate()
    return


try:
    while proc_lst:
        #TODO check if any of the processes exit abnormally
        for i,p in enumerate(proc_lst):
            if p.poll() is not None:
                print(p.stdout.read(), end='')
                p.stdout.close()
                print("Process ended unexpectedly with path: ",path_lst[i])
                proc_lst.remove(p)
                safe_termination(proc_lst)
                sys.exit(1)
                # TODO Attempt to restart process
                # p = Popen(path_lst[i], **kwds)

        # Read stdout
        try:
            r_list = select([p.stdout for p in proc_lst], [], []) [0]
            for f in r_list:
                print(f.readline(), end='')
        except ValueError as e:
            print("[ERROR]", e)
except KeyboardInterrupt:
    safe_termination(proc_lst)