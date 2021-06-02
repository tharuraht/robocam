# Python (partially complete) code to change network live based on speed
import speedtest
import subprocess
import time

all_intf = ["eth0, ..., ethn"]

def update_priority(intf, prev_intf = None):
    # TODO Set new intf metric lower than the previous intf
    pass

def get_intf_addr():
    #TODO  Get interface source address
    pass

def get_cur_intf_speed(intf):
    #TODO get current interface speed, e.g. by using TShark to measure upload rate
    pass

def measure_intfs(cur_intf = ''):
    best_intf = ''
    best_speed = 0
    for intf in all_intf:
        if intf is not cur_intf: # Only test non-current interfaces
            intf_addr = get_intf_addr()

            s = speedtest.Speedtest(source_address = intf_addr)
            s.get_best_server()
            bps = s.upload() # Measure upload speed in bps

            if bps > best_speed:
                best_speed = bps
                best_intf = intf

    return best_intf, best_speed


cur_intf, _ = measure_intfs() # Get best interface
update_priority(cur_intf) # Change priority to use

while True:
    time.sleep(30) # Only update every 30 seconds
    rest_best, rest_speed = measure_intfs(cur_intf) # Get best of the rest

    cur_speed = get_cur_intf_speed(cur_intf)

    if rest_speed > cur_speed:
        update_priority(rest_best, cur_intf)
        cur_intf = rest_best




