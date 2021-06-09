#!/usr/bin/python3
# http://lifestyletransfer.com/how-to-launch-gstreamer-pipeline-in-python/

import sys
import gi
import random
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
import iperf_data

#HOSTIP = "192.168.0.99"
HOSTIP = "77.101.164.194"
# BITRATE = "2000000"
STREAM_PARAMS = "framerate=25/1,width=1280,height=720"

bitrate = 2000000
rates = [2000, 20000, 200000, 2000000]
random.seed()
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

def set_bitrate(pipeline):
    global bitrate
    print("Setting bitrate to {0}".format(bitrate))
    videosrc.set_property("bitrate", bitrate)
    videosrc.set_property("annotation-text", "Bitrate %d" % (bitrate))
    # TODO define steps, step through each step after test
    # bitrate += 10
    # bitrate = random.choice(rates)
    net_bitrate = iperf_data.run_udp_speedtest(HOSTIP,duration=3)
    # TODO look for a good scaling
    print(f"Net bit-rate {net_bitrate}")
    bitrate = min(65535,0.7*net_bitrate)
    return True


if __name__ == "__main__":
    # GObject.threads_init()
    # initialization
    loop = GLib.MainLoop()
    Gst.init(None)

    # pipeline = Gst.parse_launch ("rpicamsrc name=src ! video/x-h264,width=320,height=240 ! h264parse ! mp4mux ! filesink name=s")
    pipeline = Gst.parse_launch(f"\
    rpicamsrc preview=false rotation=180 annotation-mode=time+date name=src \
    ! video/x-h264,{STREAM_PARAMS} \
    ! h264parse \
    ! queue \
    ! rtph264pay config-interval=1 pt=96 \
    ! gdppay \
    ! udpsink host={HOSTIP} port=5000")

    if pipeline == None:
      print ("Failed to create pipeline")
      sys.exit(0)

    # watch for messages on the pipeline's bus (note that this will only
    # work like this when a GLib main loop is running)
    bus = pipeline.get_bus()
    bus.add_watch(0, bus_call, loop)

    videosrc = pipeline.get_by_name ("src")
    videosrc.set_property("bitrate", bitrate)
    # videosrc.set_property("saturation", saturation)
    videosrc.set_property("annotation-mode", 1)

    # this will call set_saturation every 10s
    GLib.timeout_add(10000, set_bitrate, pipeline)

    # run
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except Exception as e:
        print(e)
    # cleanup
    pipeline.set_state(Gst.State.NULL)
