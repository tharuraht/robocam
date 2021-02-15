#!/usr/bin/python3
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

def bus_call(bus, msg, *args):
    # print("BUSCALL", msg, msg.type, *args)
    if msg.type == Gst.MessageType.EOS:
        print("End-of-stream")
        loop.quit()
        return
    elif msg.type == Gst.MessageType.ERROR:
        print("GST ERROR", msg.parse_error())
        loop.quit()
        return
    return True


if __name__ == "__main__":
    # initialization
    loop = GLib.MainLoop()
    Gst.init(None)

    # pipeline = Gst.parse_launch ("rpicamsrc name=src ! video/x-h264,width=320,height=240 ! h264parse ! mp4mux ! filesink name=s")
    pipeline = Gst.parse_launch("\
    udpsrc port=5000 name=src \
    ! gdpdepay \
    ! rtph264depay \
    ! avdec_h264 \
    ! videoconvert \
    ! autovideosink sync=false");

    if pipeline == None:
      print ("Failed to create pipeline")
      sys.exit(0)

    # watch for messages on the pipeline's bus (note that this will only
    # work like this when a GLib main loop is running)
    bus = pipeline.get_bus()
    bus.add_watch(0, bus_call, loop)
    # run
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except Exception as e:
        print(e)
    # cleanup
    pipeline.set_state(Gst.State.NULL)