#!/usr/bin/python3
# #SERVER=4grobo.zapto.org
# SERVER=10.200.200.1

# gst-launch-1.0 rpicamsrc annotation-mode=time preview=false vflip=true bitrate=100000 keyframe-interval=-1 ! \
# 	video/x-h264, framerate=25/1, height=720, width=1280 ! h264parse ! \
# 	rtspclientsink debug=true protocls=udp-mcast+udp location=rtsp://$SERVER:5000/test latency=0 ulpfec-percentage=10

# http://lifestyletransfer.com/how-to-launch-gstreamer-pipeline-in-python/

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
import json
import socket
import os
import logging


def percent_change(current, previous):
    if current == previous:
        return 100.0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0

class video_streamer:
     # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    # bitrate = 0
    rate_scaling_factor = 1.2

    def __init__(self, conf):
        self.conf = conf
        self.bitrate = conf['pi']['starting_bitrate']
        self.diff_threshold = 5
        self.old_recv_bitrate = 0

    def bus_call(self, bus, msg, *args):
        # print("BUSCALL", msg, msg.type, *args)
        if msg.type == Gst.MessageType.EOS:
            logging.info("End-of-stream")
            self.loop.quit()
            return
        elif msg.type == Gst.MessageType.ERROR:
            logging.error("GST ERROR %s", msg.parse_error())
            self.loop.quit()
            sys.exit(1)
        elif msg.type == Gst.MessageType.STREAM_START:
            logging.info("Stream Started!")
        return True

    def set_bitrate(self, videosrc):
        bitrate, jitter = self.get_rec_stats()

        if bitrate != self.old_recv_bitrate:
            logging.debug(f"Receiver bitrate {bitrate} jitter {jitter}")
            new_rate = self.scaled_bitrate(bitrate, jitter)
            # logging.debug(f"New rate: {new_rate}")

            # Update if non-zero and more than threshold% different to previous
            if new_rate and percent_change(new_rate, self.bitrate) > self.diff_threshold:
                self.bitrate = new_rate
                # self.bitrate = 1000000
                # print('Configured next bitrate set to', self.bitrate)


                logging.debug("Updating video bitrate to {0}".format(self.bitrate))
                videosrc.set_property("bitrate", self.bitrate)
                videosrc.set_property("annotation-text", "Bitrate %d  " % (self.bitrate))
        self.old_recv_bitrate = bitrate
        return True

    def get_rec_stats(self):
        try:
            with open("rec_stats.tmp","r") as f:
                data = json.load(f)
                #print("json data: %s" % data)
                if data['KEY'] == 'RTCP_STATS':
                    bitrate, jitter = data['PARAMS']
                    #print(int(bitrate),int(jitter))
                    return int(bitrate),int(jitter)
        except Exception as e:
            # print(e)
            logging.warning(e)
        
        return 0,0


    def scaled_bitrate(self, rate, jitter):
        #TODO use jitter to drop even more?

        new_rate = min(int(rate), 25000000)
        
        # logging.debug("new rate before %0d" % new_rate)
        # if jitter > 300:
        #     new_rate = int(new_rate/2)
        # else:
        #     new_rate = int(new_rate*self.rate_scaling_factor)
        if jitter < 300:
            new_rate = int(new_rate*self.rate_scaling_factor)
        else:
            new_rate = int(new_rate/2)
        
        # logging.debug("new rate after %0d" % new_rate)
        return new_rate


    def launch(self):
        hostip = self.conf['host']['stream_hostname']
        hostport = self.conf['host']['stream_rec_port']
        fec = self.conf['pi']['fec_percentage']
        stream_params = self.conf['pi']['stream_params']

        pipeline = Gst.parse_launch(f'\
        rpicamsrc preview=false vflip=true annotation-mode=time+date+custom-text name=src \
        bitrate={self.bitrate} annotation-text=\"Bitrate {self.bitrate} \" \
        ! video/x-h264,{stream_params} \
        ! h264parse \
        ! queue \
        ! rtspclientsink debug=true protocols=udp-mcast+udp \
        location=rtsp://{hostip}:{hostport}/test latency=0 ulpfec-percentage={fec}')

        if pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        videosrc = pipeline.get_by_name ("src")
        # videosrc.set_property("bitrate", self.bitrate)

        GLib.timeout_add(1000, self.set_bitrate, videosrc)

        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        finally:
            # cleanup
            pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    
    # Configure Logger
    logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
        level=logging.getLevelName(conf['log_level']))

    streamer = video_streamer(conf)
    streamer.launch()
    print("FINSIHED")
