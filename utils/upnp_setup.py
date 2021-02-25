#! /usr/bin/env python
# https://github.com/miniupnp/miniupnp/blob/master/miniupnpc/testupnpigd.py
# $Id: testupnpigd.py,v 1.7 2020/04/06 10:23:02 nanard Exp $
# MiniUPnP project
# Author : Thomas Bernard
# This Sample code is public domain.
# website : https://miniupnp.tuxfamily.org/

# import the python miniupnpc module
import miniupnpc
import socket

class upnp_port():
  u = miniupnpc.UPnP()
  port = None
  eport = None

  def __init__(self, port):
    self.u.discoverdelay = 200
    self.port = port
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

    try:
      print('Discovering... delay=%ums' % self.u.discoverdelay)
      ndevices = self.u.discover()
      print(ndevices, 'device(s) detected')

      # select an igd
      self.u.selectigd()
      # display information about the IGD and the internet connection
      print('local ip address :', self.u.lanaddr)
      externalipaddress = self.u.externalipaddress()
      print('external ip address :', externalipaddress)
      print(self.u.statusinfo(), self.u.connectiontype())

      eport = self.port

      # find a free port for the redirection
      r = self.u.getspecificportmapping(eport, 'TCP')
      while r != None and eport < 65536:
        eport = eport + 1
        r = self.u.getspecificportmapping(eport, 'TCP')

      print('trying to redirect %s port %u TCP => %s port %u TCP' % (externalipaddress, eport, self.u.lanaddr, self.port))

      b = self.u.addportmapping(eport, 'TCP', self.u.lanaddr, self.port,
                          'UPnP IGD Tester port %u' % eport, '')
      if b:
        print('Success')
        self.eport = eport
      else:
        print('Failed')

    except Exception as e:
      print('Exception :', e)

  def close_port(self) -> bool:
    b = self.u.deleteportmapping(self.eport, 'TCP')
    if b:
      print('Successfully deleted port mapping')
    else:
      print('Failed to remove port mapping')


def force_close(port):
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

  u.deleteportmapping(port, 'TCP')

if __name__ == '__main__':
  u = upnp_port(5002)
  try:
    while True: pass
  except KeyboardInterrupt as details:
    print("CTRL-C exception!", details)
  u.close_port()
    
