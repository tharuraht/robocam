#!/usr/bin/python3
# http://lifestyletransfer.com/how-to-launch-gstreamer-pipeline-in-python/

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
from multiprocessing import Process
import json
import socket
import os


class video_streamer:
     # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    # bitrate = 0
    rate_scaling_factor = 0.7

    def __init__(self, conf):
        self.conf = conf
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
        elif msg.type == Gst.MessageType.STREAM_START:
            print("Stream Started!")
        return True
    
    def set_bitrate(self, videosrc):
        print("Updating video bitrate to {0}".format(self.bitrate))
        videosrc.set_property("bitrate", self.bitrate)
        # videosrc.set_property("annotation-text", "Bitrate %d" % (self.bitrate))

        new_rate = 0
        if os.path.exists('net_bitrate.tmp'):
            with open('net_bitrate.tmp', 'r') as f:
                val = f.read()
                new_rate = self.scaled_bitrate(float(val))
        
        if new_rate and self.bitrate != new_rate:
            self.bitrate = new_rate
            print('Configured next bitrate set to', self.bitrate)
        return True
    
    def scaled_bitrate(self, rate):
        return min(int(self.rate_scaling_factor*rate), GLib.MAXINT)

    
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
        ! queue \
        ! tcpclientsink host={hostip} port=5000")

        if pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        videosrc = pipeline.get_by_name ("src")
        videosrc.set_property("bitrate", self.bitrate)

        GLib.timeout_add(5000, self.set_bitrate, videosrc)

        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        finally:
            # cleanup
            pipeline.set_state(Gst.State.NULL)


def write_bitrate(rate):
    print(rate)
    with open('net_bitrate.tmp','w') as f:
        f.write(rate)


def bitrate_parser(conf):
    #TODO send encrypted
    tcp_ip = conf['pi']['vpn_addr']
    tcp_port = conf['pi']['comms_port']

    print(f'Hosting server on {tcp_ip}:{tcp_port}')

    buffer_sz = 100

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', tcp_port))
    s.listen()
    print("Server is open to connections")


    while True:
        try:
            conn, addr = s.accept()
            # print("Connection address:", addr)
            if addr[0] == conf['host']['vpn_addr']:
                while True:
                    data=conn.recv(buffer_sz)
                    if data:
                        # print("Received data:", data)
                        msg = data.decode('utf-8')
                        # print('msg',msg)
                        ctrl, val = msg.split(':')
                        if ctrl == 'REC_BITRATE':
                            print('Setting NET rate to', val)
                            # streamer.set_new_bitrate(float(val))
                            write_bitrate(val)

                    else:
                        break
                    
            else:
                print(f'{addr} is not a valid source address')
        finally:
            conn.close()



if __name__ == "__main__":
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)

    streamer = video_streamer(conf)
    comms_proc = Process(target=bitrate_parser, args=(conf,))
    comms_proc.start()

    streamer_proc = Process(target=streamer.launch())

    streamer_proc.start()


    streamer_proc.join()
    comms_proc.terminate()
