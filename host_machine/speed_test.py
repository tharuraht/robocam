import time
import psutil

vpn_intf = 'wg0-client'
# vpn_intf = 'eth0'
def main():
    old_value = 0    
   

    while True:
        # print(io_counter)
        io_counter = psutil.net_io_counters(pernic=True, nowrap=True)
        new_value = io_counter[vpn_intf].bytes_recv
        # print(new_value)
        if old_value:
            send_stat(new_value - old_value)

        old_value = new_value

        time.sleep(1)

def convert_to_gbit(value):
    return value/1024./1024./1024.*8

def send_stat(value):
    print ("%0.3f" % convert_to_gbit(value))

main()