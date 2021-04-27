import miniupnpc
import socket
import sys
import os
import csv

assert len(sys.argv) <= 3
print(sys.argv)

mode = sys.argv[1]

if len(sys.argv) == 3:
  output = sys.argv[2]

def log_ports(ports):
  # Log the open ports
  with open("open_ports.tmp", 'w', newline='') as f:
     wr = csv.writer(f, quoting=csv.QUOTE_NONE)
     wr.writerow(ports)
  
def get_logged_ports():
  with open('open_ports.tmp', newline='') as f:
    reader = csv.reader(f)
    data = list(reader)
    return data

if mode == 'SETUP':
  print ('setup')

  #TODO check if file already there
  port_lines = output.splitlines()

  ports = []
  for line in port_lines:
    port = line.split(':')[1].strip()
    print("port",port)
    ports.append(int(port))

  print(ports)
  u = miniupnpc.UPnP()
  u.discoverdelay = 200
  mode = 'UDP'


  try:
    print('Discovering... delay=%ums' % u.discoverdelay)
    ndevices = u.discover()
    print(ndevices, 'device(s) detected')

    # select an igd
    u.selectigd()
    
    # display information about the IGD and the internet connection
    print('local ip address :', u.lanaddr)
    print('external ip address :', u.externalipaddress)
    print(u.statusinfo(), u.connectiontype())

    for port in ports:

      eport = port
      mode = 'UDP'

      # find a free port for the redirection
      r = u.getspecificportmapping(eport, mode)
      # while r != None and eport < 65536:
      #   eport = eport + 1
      #   r = u.getspecificportmapping(eport, mode)

      print('trying to redirect %s port %u => %s port %u %s' % (\
      u.externalipaddress, eport, u.lanaddr, port, mode))

      b = u.addportmapping(eport, mode, u.lanaddr, port,
                          'UPnP IGD Tester port %u' % eport, '')
      if b:
        print('Success, bound to eport %0d' % eport)
      else:
        print('Failed')
    
    #Log ports if successful
    log_ports(ports)
  except Exception as e:
    print('Exception :', e)

elif mode == 'CLOSE':
  print('close')

  if os.path.exists('open_ports.tmp'):
    port_lines = get_logged_ports()

    print ("Closing: ", port_lines)
  
    u = miniupnpc.UPnP()
    u.discoverdelay = 200
    print('Discovering... delay=%ums' % u.discoverdelay)
    ndevices = u.discover()
    print(ndevices, 'device(s) detected')

    # select an igd
    u.selectigd()

    for ports in port_lines:
      for port in ports:
        print("Releasing port",port)
        u.deleteportmapping(int(port), 'UDP')
    
    os.remove('open_ports.tmp')
  else:
    print("No open ports file")