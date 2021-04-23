import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib, GObject, GstRtspServer

Gst.init(None)


def tmp(factory):
  print('hi')
  print(factory.__dict__)


class RTSP_Server:
  port = "5000"
  mount_point = "/test"

  PIPELINE = "rtpjitterbuffer drop-on-latency=true latency=0 name=depay0 ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink"

  def media_prepared_cb(self, media):
    n_streams = media.n_streams()
    print("Media %s is prepared and has %0d streams" % (media, n_streams))

    for i in range(n_streams):
      stream = media.get_stream(i)

      if stream is None:
        continue
      
      session = stream.get_rtpsession()
      print("Watching session %s on stream %0d" % (session,i))

      session.connect("on-ssrc-active", on_ssrc_active)

  def media_configure_cb(self, factory, media):
    media.connect("prepared", media_prepared_cb)

  
  def factory_setup(self):
    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_transport_mode(GstRtspServer.RTSPTransportMode.RECORD)
    factory.set_launch(self.PIPELINE)
    # factory.latency = 0
    # print(factory.__dict__)

    #Callback to start tracing once media is prepared for streaming
    factory.connect("media-configure", self.media_configure_cb)
    return factory

  def launch():
    server = GstRtspServer.RTSPServer.new()
    server.set_service(self.port)
    mounts = server.get_mount_points()
    factory = self.factory_setup()

    # Dont reference factory after this point
    mounts.add_factory(self.mount_point, factory)
    server.attach()

    #  start serving
    print ("stream ready at rtsp://127.0.0.1:" + port + "/test");

    loop = GLib.MainLoop()
    loop.run()
