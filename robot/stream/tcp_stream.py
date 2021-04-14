#!/usr/bin/python3
# http://lifestyletransfer.com/how-to-launch-gstreamer-pipeline-in-python/

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
from multiprocessing import Process
import json
import socket


class video_streamer:
     # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    bitrate = 0

    def __init__(self):
        with open("robocam_conf.json") as conf_file:
            self.conf = json.load(conf_file)
        self.bitrate = 2000000
    
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
    
    def set_bitrate(self, pipeline):
        print("Setting bitrate to {0}".format(self.bitrate))
        videosrc.set_property("bitrate", self.bitrate)
        videosrc.set_property("annotation-text", "Bitrate %d" % (self.bitrate))

        new_rate = min(int(0.3*net_bitrate), GLib.MAXINT)
        print(f'Setting new rate to {self.new_rate}')
        # print('Max int ', GLib.MAXINT) 
        self.bitrate = self.new_rate
        return True
    
    def set_new_bitrate(self, rate):
        self.new_rate = rate
    
    def launch(self):
        hostip = self.conf['host']['stream_hostname']
        stream_params = self.conf['pi']['stream_params']

        pipeline = Gst.parse_launch(f"\
        rpicamsrc preview=true rotation=180 annotation-mode=time+date name=src \
        ! video/x-h264,{stream_params} \
        ! h264parse \
        ! queue \
        ! rtph264pay config-interval=1 pt=96 \
        ! gdppay \
        ! tcpclientsink host={hostip} port=5000")

        if pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = pipeline.get_bus()
        bus.add_watch(0, bus_call, loop)

        videosrc = pipeline.get_by_name ("src")
        videosrc.set_property("bitrate", bitrate)

        GLib.timeout_add(10000, self.set_bitrate, pipeline)

        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        # cleanup
        pipeline.set_state(Gst.State.NULL)

def bitrate_parser(streamer):
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    tcp_ip = "127.0.0.1"
    tcp_port = conf['pi']['comms_port']

    buffer_sz = 100

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_ip, tcp_port))
    s.listen(1)

    try:
        while True:
            conn, addr = s.accept()
            print("Connection address:", addr)
            while True:
                data=conn.recv(buffer_sz)
                if not data:
                    break
                print("Received data:", data)
            conn.close()
    except KeyboardInterrupt:
        conn.close()



if __name__ == "__main__":
    streamer = video_streamer()
    streamer_proc = Process(target=streamer.launch())
    comms_proc = Process(target=bitrate_parser.launch(), args=(streamer))

    streamer_proc.start()
    comms_proc.start()

    streamer_proc.join()
    comms_proc.terminate()
