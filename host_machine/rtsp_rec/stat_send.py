# Checks for new statistics, encrypts, serialises and sends to Pi control

# import logging
import sys
import time
import json
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import socket
import os
import logging

class StatsFile(FileSystemEventHandler):
    def __init__(self, path, conf):
      super().__init__()
      self.path = path
      self.conf = conf
      self.prev_data = ""


    # Event handlers
    def catch_all_handler(self, event):
        # logging.debug(event)
        pass

    def on_moved(self, event):
        self.catch_all_handler(event)

    def on_created(self, event):
        self.catch_all_handler(event)

    def on_deleted(self, event):
        self.catch_all_handler(event)

    def on_modified(self, event):
        self.catch_all_handler(event)


        # logging.debug("File Modified")

        with open(path,"r") as f:
          data = f.read()
          if data != self.prev_data:
            json_dump = self.json_dump(data)
            self.send(json_dump)
            self.prev_data = data
    
    def json_dump(self,data):
      dump_dict = {
        'KEY' :     'RTCP_STATS',
        'PARAMS':   data.split(','),
        'PROTOCOL': 'UDP',
        'DESC':     "RTSP Server Bitrate and Jitter to inform bitrate and fps of Rpi."   
      }
      return json.dumps(dump_dict)
    
    def send(self, data):
      addr = conf['pi']['vpn_addr']
      port = conf['pi']['comms_port']
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      logging.debug("Sending %s\nto %s:%s" % (data,addr,port))
      sock.sendto(data.encode('utf-8'),(addr, port))



path = "rec_stats.tmp"
period = 0.5

with open("robocam_conf.json") as conf_file:
    conf = json.load(conf_file)

# Configure Logger
logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
    level=logging.getLevelName(conf['log_level']))

# Wait until file created
while not os.path.exists(path):
  time.sleep(0.5)


stats_file_handler = StatsFile(path,conf)
observer = Observer()
observer.schedule(stats_file_handler, path, recursive=False)
observer.start()
try:
    while True:
        time.sleep(period)
finally:
    observer.stop()
    observer.join()