#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib, GObject, GstRtspServer, Gio, GstRtsp
import subprocess
import upnp_rtsp

Gst.init(None)
Gst.debug_set_active(True)
# Gst.debug_set_default_threshold(3)

# # Helper functions
# def open_ports():
#   """
#   Discovers ports opened by program and opens them on router via UPnP
#   """
#   print("OPEN PORETS")
#   p=subprocess.run(["lsof -i4 -n | grep UDP"], shell=True, stdout=subprocess.PIPE, universal_newlines=True)
#   port_lines = p.stdout.splitlines()

#   ports = []
#   for line in port_lines:
#     port = line.split(':')[1].strip()
#     ports.append(int(port))
  
#   print("Opening ports", ports)
#   upnp_rtsp.open_upnp_ports(ports)


class RTSP_Server:
  port = "5000"
  mount_point = "/test"
  latency = 100

  PIPELINE = "\
  rtph264depay name=depay0\
  ! avdec_h264 \
  ! videoconvert \
  ! autovideosink"



  def on_ssrc_active(self, session, source):
    # Open RTP ports on router via upnp
    # open_ports()

    stats = source.get_property("stats")
    is_sender = stats.get_boolean("is-sender")
    # print(is_sender)
    if is_sender[1]:
      bitrate = stats.get_uint64("bitrate")
      jitter = stats.get_uint("jitter")
      # print(bitrate[1],jitter[1])
      data = f"{bitrate[1]},{jitter[1]}"
      with open("rec_stats.tmp","w") as f:
        f.write(data)
    
    # twcc_stats = source.get_property("twcc-stats")
    # print("TWCC stats:",twcc_stats)

  def media_prepared_cb(self, media):
    n_streams = media.n_streams()
    print("Media %s is prepared and has %0d streams" % (media, n_streams))

    for i in range(n_streams):
      stream = media.get_stream(i)

      if stream is None:
        continue
      
      session = stream.get_rtpsession()
      print("Watching session %s on stream %0d" % (session,i))

      # print(dir(stream))
      # rtcp_range = stream.get_server_port(Gio.SocketFamily.IPV4)
      # print("rtcp ports", rtcp_range.to_string(GstRtsp.RTSPTimeRange))
      # print("rtp socket", stream.get_rtp_socket(Gio.SocketFamily.IPV4))

      session.connect("on-ssrc-active", self.on_ssrc_active)



  def media_configure_cb(self, factory, media):
    media.connect("prepared", self.media_prepared_cb)

  
  def factory_setup(self):
    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_transport_mode(GstRtspServer.RTSPTransportMode.RECORD)
    factory.set_launch(self.PIPELINE)
    factory.set_latency(self.latency)

    #Callback to start tracing once media is prepared for streaming
    factory.connect("media-configure", self.media_configure_cb)
    return factory

  def launch(self):
    server = GstRtspServer.RTSPServer.new()
    server.set_service(self.port)
    mounts = server.get_mount_points()
    factory = self.factory_setup()

    # Dont reference factory after this point
    mounts.add_factory(self.mount_point, factory)
    server.attach()

    #  start serving
    print ("stream ready at rtsp://127.0.0.1:" + self.port + "/test");

    loop = GLib.MainLoop()
    loop.run()

if __name__ == '__main__':
  server = RTSP_Server()
  server.launch()