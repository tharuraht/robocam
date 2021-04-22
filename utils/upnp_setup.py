#! /usr/bin/env python3
# https://github.com/miniupnp/miniupnp/blob/master/miniupnpc/testupnpigd.py
# $Id: testupnpigd.py,v 1.7 2020/04/06 10:23:02 nanard Exp $
# MiniUPnP project
# Author : Thomas Bernard
# This Sample code is public domain.
# website : https://miniupnp.tuxfamily.org/

# import the python miniupnpc module
import miniupnpc
import socket
import sys

class upnp_port():
  u = miniupnpc.UPnP()
  port = None
  eport = None
  mode = None
  lanoverride = None

  def __init__(self, port, mode='TCP', lanoverride = None):
    self.u.discoverdelay = 200
    self.port = port
    self.mode = mode
    self.lanoverride = lanoverride
    self.open_port()
    

  def open_port(self):
    """
    Create miniupnpc object and open port on router.
    Returns object, and external port.
    """
    # create the object
    #print 'inital(default) values :'
    #print ' discoverdelay', self.u.discoverdelay
    #print ' lanaddr', self.u.lanaddr
    #print ' multicastif', self.u.multicastif
    #print ' minissdpdsocket', self.u.minissdpdsocket

    if self.lanoverride != None:
      lanaddr = self.lanoverride
    else:
      lanaddr = self.u.lanaddr
      lanaddr = '192.168.0.99'

    try:
      print('Discovering... delay=%ums' % self.u.discoverdelay)
      ndevices = self.u.discover()
      print(ndevices, 'device(s) detected')

      # select an igd
      self.u.selectigd()
      
      # display information about the IGD and the internet connection
      print('local ip address :', lanaddr)
      externalipaddress = self.u.externalipaddress()
      # externalipaddress = '185.69.144.86'
      print('external ip address :', externalipaddress)
      print(self.u.statusinfo(), self.u.connectiontype())

      eport = self.port

      # find a free port for the redirection
      r = self.u.getspecificportmapping(eport, self.mode)
      while r != None and eport < 65536:
        eport = eport + 1
        r = self.u.getspecificportmapping(eport, self.mode)

      print('trying to redirect %s port %u => %s port %u %s' % (externalipaddress, eport, lanaddr, self.port, self.mode))

      b = self.u.addportmapping(eport, self.mode, lanaddr, self.port,
                          'UPnP IGD Tester port %u' % eport, '')
      if b:
        print('Success, bound to eport %0d' % eport)
        self.eport = eport
      else:
        print('Failed')

    except Exception as e:
      print('Exception :', e)

  def close_port(self) -> bool:
    if self.eport is not None:
        b = self.u.deleteportmapping(self.eport, self.mode)
        if b:
            print('Successfully deleted port mapping')
        else:
            print('Failed to remove port mapping')
    else:
        print("Port was not bound")


def force_close(port, mode = 'TCP'):
  """
  Finds IGD and attempts to close port
  """
  u = miniupnpc.UPnP()
  u.discoverdelay = 200
  print('Discovering... delay=%ums' % u.discoverdelay)
  ndevices = u.discover()
  print(ndevices, 'device(s) detected')

  # select an igd
  u.selectigd()

  u.deleteportmapping(port, mode)

if __name__ == '__main__':
  #u = upnp_port(5002, 'TCP')
  print(sys.argv)
  u_list = []
  for i in range(1,len(sys.argv)):
      u = upnp_port(int(sys.argv[i]), 'UDP')
      u_list.append(u)
  try:
    while True: pass
  except KeyboardInterrupt as details:
    print("CTRL-C exception!", details)
  #u.close_port()
  for u in u_list:
      print("Closing port %0d" % u.port)
      u.close_port()
    
