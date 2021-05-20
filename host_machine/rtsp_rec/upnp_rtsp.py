#!/usr/bin/env python3
import miniupnpc
import socket
import sys
import os
import csv
import json
import logging

with open("robocam_conf.json") as f:
  conf = json.load(f)
logging.basicConfig(format=conf['log_format'], \
  level=logging.getLevelName(conf['log_level']))

def log_ports(ports):
  # Log the open ports
  with open("tmp/open_ports.tmp", 'w', newline='') as f:
     wr = csv.writer(f, quoting=csv.QUOTE_NONE)
     wr.writerow(ports)
  
def get_logged_ports():
  with open('tmp/open_ports.tmp', newline='') as f:
    reader = csv.reader(f)
    data = list(reader)
    flat_data = [item for sublist in data for item in sublist]
    return flat_data


def open_ports(ports):
  u = miniupnpc.UPnP()
  u.discoverdelay = 200
  mode = 'UDP'


  try:
    # print('Discovering... delay=%ums' % u.discoverdelay)
    ndevices = u.discover()
    # print(ndevices, 'device(s) detected')

    # select an igd
    u.selectigd()
    
    # display information about the IGD and the internet connection
    logging.debug('local ip address : %s'% u.lanaddr)
    logging.debug('external ip address : %s'% u.externalipaddress)
    logging.debug(f"{u.statusinfo()}, {u.connectiontype()}")

    for port in ports:
      mode = 'UDP'
      # find a free port for the redirection
      r = u.getspecificportmapping(port, mode)
      b = u.addportmapping(port, mode, u.lanaddr, port,
                          'Robocam UPnP IGD port %u' % port, '')
      if b:
        logging.info('Success, bound to eport %0d' % port)
      else:
        logging.warning('Failed')
    
    #Log ports if successful
    log_ports(ports)
  except Exception as e:
    logging.exception(('Exception : %s' % e))

def close_ports():
  if os.path.exists('tmp/open_ports.tmp'):
    ports = get_logged_ports()

    logging.info("Closing: ", ports)
  
    u = miniupnpc.UPnP()
    u.discoverdelay = 200
    # print('Discovering... delay=%ums' % u.discoverdelay)
    ndevices = u.discover()
    # print(ndevices, 'device(s) detected')

    # select an igd
    u.selectigd()

    for port in ports:
      # print("Releasing port",port)
      u.deleteportmapping(int(port), 'UDP')
    
    os.remove('tmp/open_ports.tmp')
  else:
    logging.warning("No open ports file")


def open_upnp_ports(ports):
  #If file exists, check old ports first
  if os.path.exists('tmp/open_ports.tmp'):
    logging.debug ("File found checking...")
    old_ports = get_logged_ports()

    old_ports = list(map(int, old_ports)) # converts strings to ints
    # print(set(ports), set(old_ports))
    if set(ports) != set(old_ports):
      logging.debug('New ports defined, removing old ports...')
      close_ports()
      open_ports(ports)
    else:
      logging.debug("Same ports, no change needed")
  else:
    open_ports(ports)

def open_new_ports(output):
  logging.debug(output)
  port_lines = output.splitlines()

  ports = []
  for line in port_lines:
    port = line.split(':')[1].strip()
    # print("port",port)
    ports.append(int(port))

  logging.info(f"Opening ports: {ports}")
  open_upnp_ports(ports)


if __name__ == '__main__':

  assert len(sys.argv) <= 3
  # print(sys.argv)

  mode = sys.argv[1]

  if len(sys.argv) == 3:
    output = sys.argv[2]


  if mode == 'SETUP':
    logging.info('Setting up RTSP upnp ports...')
    open_new_ports(output)

  elif mode == 'CLOSE':
    logging.info('Closing ports')
    close_ports()
  else:
    raise Exception("Invalid Mode")
