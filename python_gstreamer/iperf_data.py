#!/usr/bin/python3
# https://buildmedia.readthedocs.org/media/pdf/iperf3-python/latest/iperf3-python.pdf
# https://iperf3-python.readthedocs.io/en/latest/modules.html
import json
import sys
import subprocess
import iperf3

# iperf3 -c 77.101.164.194 -p 5000 -u -b 1000000000 -J -t 5 > perf.json

def run_udp_speedtest(hostname, bandwidth=1000000000, duration=5):
  client = iperf3.Client()
  client.duration = duration
  client.server_hostname = hostname
  client.port = 5001
  client.protocol = 'udp'
  client.bandwidth = bandwidth

  print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
  result = client.run()
  if result.error:
    print(result.error)
    return 0
  else:
    # print('')
    # print('Test completed:')
    # print(' started at {0}'.format(result.time))
    # print(' bytes transmitted {0}'.format(result.bytes))
    # print(' jitter (ms) {0}'.format(result.jitter_ms))
    # print(' avg cpu load {0}%\n'.format(result.local_cpu_total))
    print('Average transmitted data in all sorts of networky formats:')
    # print(' bits per second (bps) {0}'.format(result.bps))
    # print(' Kilobits per second (kbps) {0}'.format(result.kbps))
    print(' Megabits per second (Mbps) {0}'.format(result.Mbps))
    # print(' KiloBytes per second (kB/s) {0}'.format(result.kB_s))
    # print(' MegaBytes per second (MB/s) {0}'.format(result.MB_s))

      
    return min_bitrate(result.json)


def min_bitrate(data):
  min_rate = None

  for interval in data['intervals']:
    rate = interval['streams'][0]['bits_per_second']
    # print(rate)
    # print(interval)
    if min_rate is None or rate < min_rate:
      min_rate = rate

  if min_rate is None:
    return 0
  else:
    return min_rate

def main(argv):
  with open (argv) as f:
    data = json.load(f)
    # ret = min_bitrate(data)
    # print(data['intervals'])
  # ret = min_bitrate(argv)
  ret = run_udp_speedtest('77.101.164.194')
  print(f"Min bit-rate: {ret}")

if __name__ == "__main__":
  assert(len(sys.argv) == 2)
  main(sys.argv[1])
