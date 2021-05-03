import psutil
import time
import statistics
import math
from enum import Enum
import json
import socket

with open("robocam_conf.json") as conf_file:
    conf = json.load(conf_file)
intf = 'wg0'
measure_time = 1
period = 0.03
repeats = int(measure_time/period)

print("No. of measurements:", repeats)


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

def measure():
  rates= []
  try:
    for _ in range(repeats):
      # print(iostat['wg0'].bytes_recv)
      start_count = psutil.net_io_counters(pernic=True)[intf].bytes_recv
      time.sleep(period)
      end_count =  psutil.net_io_counters(pernic=True)[intf].bytes_recv
      rate = int(8*((end_count - start_count)/period))
      # print(rate)
      rates.append(rate)
  finally:
    print(rates)
    return rates

def analyse(bitrates):
  start = bitrates[0]
  median = bitrates[int(len(bitrates)/2)]
  end = bitrates[-1]

  print(start,median,end)
  
  if start <= median <= end:
    print('Monotonicaly increasing')
    return Observation.beta
  elif start >= median >= end:
    print('Monotonicaly decreasing')
    return Observation.alpha
  else:
    return Observation.gamma
  
def rms(bitrates):
  sum_squared = sum(map(lambda x:x*x,bitrates))
  return math.sqrt(sum_squared/len(bitrates))

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def find_rms(bitrates):
  total_rms = rms(bitrates)

  print("Total rms", total_rms)

  # Split into 3 parts and find each rms
  rms1, rms2, rms3 = [rms(part) for part in split(bitrates, 3)]
  print(rms1,rms2,rms3)

  # Find diff between rms of each part and total rms
  diff1, diff2, diff3 = [(total_rms - rmsn) for rmsn in [rms1,rms2,rms3]]
  print(diff1,diff2,diff3)

  if diff1 <= diff2 <= diff3:
    return 1
  elif diff1 >= diff2 >= diff3:
    return 0
  else:
    return 2

def json_dump(data):
  dump_dict = {
    'KEY' :     'BITRATE_STATE',
    'PARAMS':   data,
    'PROTOCOL': 'UDP',
    'DESC':     ""   
  }
  return json.dumps(dump_dict)


def send(data):
  addr = conf['pi']['vpn_addr']
  port = conf['pi']['comms_port']
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  logging.debug("Sending %s\nto %s:%s" % (data,addr,port))
  sock.sendto(data.encode('utf-8'),(addr, port))

def get_status():
  bitrates = measure()
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

  # print(L_max)
  # print(L_min)
  max_obv = analyse(L_max)
  min_obv = analyse(L_min)

  print(max_obv, min_obv)

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
    cur_rms = find_rms(bitrates)
  
  print("Status:",status)
  if status == Status.Non_Monotonic:
    print("Current rms state:",cur_rms)

  return status, cur_rms

def main():
  tcp_port = conf['host']['comms_port']

  print(f'Hosting server on port {tcp_port}')
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.settimeout(1.0)
  s.bind(('', tcp_port))
  s.listen()
  print("Server is open to connections")
  conn = None

  while True:
      try:
          conn, addr = s.accept()
      except socket.timeout as e:
          continue
      # print("Connection address:", addr)
      if addr[0] == conf['pi']['vpn_addr']:
          # Measure bitrate and send to pi
          status, cur_rms = get_status()
          # Serialise and send to pi
          dump = json_dump([f"{status}", cur_rms])
          print('Sending', dump)
          conn.sendall(dump.encode('utf-8'))
      else:
          print(f'{addr} is not a valid source address')
      conn.close()

  s.shutdown(1)
  s.close()


if __name__ == '__main__':
  main()