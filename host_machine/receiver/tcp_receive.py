#!/usr/bin/python3
import sys
import gi
import iperf3
from multiprocessing import Process
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


class video_receiver:
    # initialization
    loop = GLib.MainLoop()
    Gst.init(None)

    def bus_call(self, bus, msg, *args):
        # print("BUSCALL", msg, msg.type, *args)
        if msg.type == Gst.MessageType.EOS:
            print("End-of-stream")
            self.loop.quit()
            return
        elif msg.type == Gst.MessageType.ERROR:
            print("GST ERROR", msg.parse_error())
            self.loop.quit()
            return
        return True

    def launch(self):

        # pipeline = Gst.parse_launch ("rpicamsrc name=src ! video/x-h264,width=320,height=240 ! h264parse ! mp4mux ! filesink name=s")
        pipeline = Gst.parse_launch("\
        tcpserversrc port=5000 host=192.168.0.99 name=src \
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
        bus.add_watch(0, self.bus_call, self.loop)
        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        # cleanup
        pipeline.set_state(Gst.State.NULL)

def start_video_receiver():
    rec = video_receiver()
    rec.launch()

def start_iperf_server():
    server = iperf3.Server()
    server.port=5001
    
    # Run function terminates each time a test completes
    while True:
        result = server.run()

if __name__ == "__main__":
    rec_stream = Process(target=start_video_receiver)
    iperf_server = Process(target=start_iperf_server)
    rec_stream.start()
    iperf_server.start()

    rec_stream.join()
    iperf_server.terminate()

