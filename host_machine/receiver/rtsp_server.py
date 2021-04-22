import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib, GObject, GstRtspServer

Gst.init(None)


def tmp(factory):
  print('hi')
  print(factory.__dict__)

port = "5000"
mount_point = "/test"

PIPELINE = "rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink"

server = GstRtspServer.RTSPServer.new()
server.set_service(port)
mounts = server.get_mount_points()
factory = GstRtspServer.RTSPMediaFactory.new()
factory.set_transport_mode(GstRtspServer.RTSPTransportMode.RECORD)
factory.set_launch(PIPELINE)
# factory.latency = 0
print(factory.__dict__)
# Dont reference factory after this point
mounts.add_factory(mount_point, factory)
server.attach()

#  start serving
print ("stream ready at rtsp://127.0.0.1:" + port + "/test");


loop = GLib.MainLoop()
loop.run()
