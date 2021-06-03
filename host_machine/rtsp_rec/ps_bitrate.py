import psutil
import time
import math
from enum import Enum
import json
import socket
import os
import logging
import select
from datetime import datetime
import statistics

def rms(bitrates):
  sum_squared = sum(map(lambda x:x*x,bitrates))
  return math.sqrt(sum_squared/len(bitrates))

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def json_dump(data):
  stats = False
  # Get current time
  t = time.localtime()
  current_time = time.strftime("%H:%M:%S", t)

  bitrate = jitter = -1
  if os.path.exists("tmp/rec_stats.tmp"):
    #Get RTCP Stats
    with open("tmp/rec_stats.tmp") as f:
      bitrate, jitter = f.readline().split(',')
      stats = True

  dump_dict = {
    'BITRATE_STATE': {
      'PARAMS':     data,
      'PROTOCOL':   'UDP',
      'DESC':       "",
      'TIMESTAMP':  current_time
    }
  }
  if stats:
    dump_dict.update({
      'RTCP_STATS': {
        'PARAMS':    [bitrate,jitter],
        'PROTOCOL': 'UDP',
        'DESC':     "RTSP Server Bitrate and Jitter to inform bitrate and fps of Rpi.",
        'TIMESTAMP': current_time
      }
    })
  return json.dumps(dump_dict)

class Status(Enum):
  Stable = 1
  Fluctuated = 2
  Degraded = 3
  Non_Monotonic = 4
  Progressive = 5

class Observation(Enum):
  alpha = 1
  beta = 2
  gamma = 3

class PS_Bitrate:
    period = 0.1
    # cached_rates stores the measure bitrates, and is consumed when bitrate 
    # is requested
    cached_rates = []

    def __init__(self, conf):
        self.conf = conf
        logging.basicConfig(format=conf['log_format'], \
        level=logging.getLevelName(conf['log_level']))
        open('rec_bitrate.csv', 'w').close() # Clear file


    def measure(self):
        intf = self.conf['host']['stream_rec_intf']

        start_count = psutil.net_io_counters(pernic=True)[intf].bytes_recv
        time.sleep(self.period)
        end_count =  psutil.net_io_counters(pernic=True)[intf].bytes_recv
        if (end_count - start_count) > 0 and len(self.cached_rates) < 1000:
            rate = int(8*((end_count - start_count)/self.period))
            if len(self.cached_rates) == 0 or rate < 2 * statistics.median(self.cached_rates):
                self.cached_rates.append(rate)
                # cur_time = datetime.now()
                with open("rec_bitrate.csv", "a") as f:
                    f.write(f"{rate}\n")
            else:
                pass


    def analyse(self, bitrates):
        if len(bitrates) == 0:
            logging.warning("Empty bitrate list!")
            return Observation.gamma
        start = bitrates[0]
        median = bitrates[int(len(bitrates)/2)]
        end = bitrates[-1]

        # logging.debug(start,median,end)
        # If all are zero, ignore
        if all(rates == 0 for rates in bitrates):
            return Observation.gamma
        
        if start <= median <= end:
            logging.debug('Monotonicaly increasing')
            return Observation.beta
        elif start >= median >= end:
            logging.debug('Monotonicaly decreasing')
            return Observation.alpha
        else:
            return Observation.gamma
    

    def find_rms(self, bitrates):
        total_rms = rms(bitrates)
        if len(bitrates) < 3:
            return 2

        logging.debug("Total rms %0d" % total_rms)


        # Split into 3 parts and find each rms
        rms1, rms2, rms3 = [rms(part) for part in split(bitrates, 3)]
        # logging.debug(rms1,rms2,rms3)

        # Find diff between rms of each part and total rms
        diff1, diff2, diff3 = [(total_rms - rmsn) for rmsn in [rms1,rms2,rms3]]
        # logging.debug(diff1,diff2,diff3)

        if diff1 <= diff2 <= diff3:
            return 1 #decreasing rms
        elif diff1 >= diff2 >= diff3:
            return 0 #increasing rms
        else:
            return 2 #unsure


    def get_status(self):
        # Fetch and clear cached bitrates
        bitrates = self.cached_rates
        self.cached_rates = []

        logging.debug(f"Cached bitrates: {bitrates}")
        L_max = []
        L_min = []

        # Find local maxima
        for i in range(len(bitrates)-1):
            v1 = bitrates[i]
            v2 = bitrates[i+1]
            v3 = bitrates[i+2] if i+2 < len(bitrates) else 0
            if max([v1,v2,v3]) == v2:
                L_max.append(v2)

        # Find local minima
        for i in range(len(bitrates)-1):
            v1 = bitrates[i]
            v2 = bitrates[i+1]
            v3 = bitrates[i+2] if i+2 < len(bitrates) else 0
            if min([v1,v2,v3]) == v2:
                L_min.append(v2)

        # print(L_max, L_min)
        max_obv = self.analyse(L_max)
        min_obv = self.analyse(L_min)
        logging.debug("%s %s" % (max_obv, min_obv))

        cur_rms = -1 # Only set when non monotonic
        if max_obv == Observation.beta and min_obv == Observation.beta:
            status = Status.Progressive
        elif max_obv == Observation.beta and min_obv == Observation.alpha:
            status = Status.Stable
        elif max_obv == Observation.alpha and min_obv == Observation.beta:
            status = Status.Fluctuated
        elif max_obv == Observation.alpha and min_obv == Observation.alpha:
            status = Status.Degraded
        else: # either is gamma
            status = Status.Non_Monotonic
            cur_rms = self.find_rms(bitrates)
        
        logging.info("Status: %s" % status)
        if status == Status.Non_Monotonic:
            logging.info("Current rms state %0d" % cur_rms)

        return status, cur_rms


    def start(self):
        tcp_port = self.conf['host']['comms_port']

        logging.info(f'Hosting server on port {tcp_port}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # s.settimeout(0.5)
        s.bind(('', tcp_port))
        s.listen()
        logging.info("Server is open to connections")
        conn = None

        timeout=0.01
        read_lst = [s]
        while True:
            readable, _, _ = select.select(read_lst, [], [], timeout)
            for r in readable:
                if r is s:
                    conn, addr = s.accept()
                    # Check address of connecting computer
                    logging.debug(f"Connection address: {addr}")
                    if addr[0] == self.conf['pi']['vpn_addr']:
                        # Measure bitrate and send to pi
                        status, cur_rms = self.get_status()
                        # Serialise and send to pi
                        dump = json_dump([str(status), cur_rms])
                        logging.debug(f'Sending {dump}')
                        conn.sendall(dump.encode('utf-8'))
                    else:
                        logging.warning(f'{addr} is not a valid source address')
                    conn.close()
            self.measure()


def main():
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    ps = PS_Bitrate(conf)
    ps.start()

if __name__ == '__main__':
    main()