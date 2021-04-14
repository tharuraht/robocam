#!/usr/bin/env python3
import pyshark
import wsutils
import re
import time
import os
import signal
import json
import socket

def get_bitrate(time=1):
  pcap_file = 'tshark_stat.pcap'

  with open("robocam_conf.json") as conf_file:
    conf = json.load(conf_file)
    host_rec_port = conf["host"]["stream_rec_port"]
    host_rec_inf = conf["host"]["stream_rec_intf"] 

  rate = 0
  os.setpgrp() # create process group, for cleanup later
  try:
    capture = pyshark.LiveCapture(
      interface = host_rec_inf, 
      output_file = pcap_file,
      only_summaries=True,
      bpf_filter = f'dst port {host_rec_port}'
      )
    capture.sniff(timeout=time)

    mypcap = wsutils.Pcap(pcap_file)
    if len(mypcap.info) > 0:
      txt = mypcap.info['Data bit rate']
      rate = float(re.findall(r'\d+\.\d+',txt)[0])

    print(f"Receiver Bit Rate: {rate} bps")

    if os.path.exists(pcap_file):
      os.remove(pcap_file)
  except Exception as e:
    os.killpg(0, signal.SIGKILL) # cleanup processes
    throw(e)
  except KeyboardInterrupt:
    os.killpg(0, signal.SIGKILL)
    if os.path.exists(pcap_file):
      os.remove(pcap_file)
  
  return rate

def send_bitrate(tcp_ip, tcp_port, rate):
  msg = f"[REC BITRATE] [{rate}]"

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((tcp_ip, tcp_port))
  s.send(msg)

if __name__ == "__main__":
  while True:
    get_bitrate(1)