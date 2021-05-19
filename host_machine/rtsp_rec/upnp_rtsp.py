#!/usr/bin/env python3
import miniupnpc
import socket
import sys
import os
import csv

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
    print('local ip address :', u.lanaddr)
    print('external ip address :', u.externalipaddress)
    print(u.statusinfo(), u.connectiontype())

    for port in ports:
      mode = 'UDP'
      # find a free port for the redirection
      r = u.getspecificportmapping(port, mode)
      b = u.addportmapping(port, mode, u.lanaddr, port,
                          'UPnP IGD Tester port %u' % port, '')
      if b:
        print('Success, bound to eport %0d' % port)
      else:
        print('Failed')
    
    #Log ports if successful
    log_ports(ports)
  except Exception as e:
    print('Exception :', e)

def close_ports():
  if os.path.exists('tmp/open_ports.tmp'):
    ports = get_logged_ports()

    print ("Closing: ", ports)
  
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
    print("No open ports file")


def open_upnp_ports(ports):
  #If file exists, check old ports first
  if os.path.exists('tmp/open_ports.tmp'):
    print ("File found checking...")
    old_ports = get_logged_ports()

    old_ports = list(map(int, old_ports)) # converts strings to ints
    # print(set(ports), set(old_ports))
    if set(ports) != set(old_ports):
      print('New ports defined, removing old ports...')
      close_ports()
      open_ports(ports)
    else:
      print("Same ports, no change needed")
  else:
    open_ports(ports)

def open_new_ports(output):
  print(output)
  port_lines = output.splitlines()

  ports = []
  for line in port_lines:
    port = line.split(':')[1].strip()
    # print("port",port)
    ports.append(int(port))

  print(ports)
  open_upnp_ports(ports)


if __name__ == '__main__':

  assert len(sys.argv) <= 3
  # print(sys.argv)

  mode = sys.argv[1]

  if len(sys.argv) == 3:
    output = sys.argv[2]


  if mode == 'SETUP':
    print ('Setting up RTSP upnp ports...')
    open_new_ports(output)

  elif mode == 'CLOSE':
    print('close')
    close_ports()
  else:
    raise Exception("Invalid Mode")
