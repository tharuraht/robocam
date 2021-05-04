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
from enum import Enum
import time

# Gst.debug_set_active(True)
# Gst.debug_set_default_threshold(3)

class Video_params:
    temporal_res = [10,15,25,30,35]
    spatial_res = [100000, 300000, 600000, 1000000, 2000000, 5000000, 7000000, 10000000]

    def __init__(self):
        self.cur_temp_idx = 3
        self.cur_spatial_idx = 1
    
    def get_temporal_res(self):
        return self.temporal_res[self.cur_temp_idx]

    def get_spatial_res(self):
        return self.spatial_res[self.cur_spatial_idx]
    
    def change_params(self,temporal=0,spatial=0):
        """
        Changes the temporal and/or spatial parameters by increment/decrement

        +1 : increment
        0  : no change
        -1 : decrement
        """
        if temporal == 1:
            if self.cur_temp_idx < len(self.temporal_res)-1:
                self.cur_temp_idx += 1
        elif temporal == -1:
            if self.cur_temp_idx > 0:
                self.cur_temp_idx -= 1

        if spatial == 1:
            if self.cur_spatial_idx < len(self.spatial_res)-1:
                self.cur_spatial_idx += 1
        elif spatial == -1:
            if self.cur_spatial_idx > 0:
                self.cur_spatial_idx -= 1
        return
        
class Status(Enum):
  Stable = 1
  Fluctuated = 2
  Degraded = 3
  Non_Monotonic = 4
  Progressive = 5

class video_streamer:
     # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    params = Video_params()


    def __init__(self, conf):
        self.conf = conf
        self.bitrate = conf['pi']['starting_bitrate']
        self.caps = self.conf['pi']['stream_params']
        self.rec_bitrate = self.rec_jitter = -1

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

    def update_framerate(self, rate):
        splits = self.caps.split(",")

        for i in range (len(splits)):
            if "framerate" in splits[i]:
                splits[i] = f"framerate={rate}/1"
        self.caps = ",".join(splits)

    def get_status(self):
        status = None
        rms_state = -1


        tcp_ip = self.conf['host']['vpn_addr']
        tcp_port = self.conf['host']['comms_port']
        buff_sz = 300

        rate = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.5)

        try:
            s.connect((tcp_ip, tcp_port))
            logging.debug('connected')
            while True:
                data = s.recv(buff_sz)
                if data:
                    msg = data.decode('utf-8')
                    # print('msg',msg)
                    dict = json.loads(msg)
                    print(dict)
                    t = time.localtime()
                    current_time = time.strftime("%H:%M:%S", t)
                    if 'BITRATE_STATE' in dict:
                        print(dict['BITRATE_STATE']['TIMESTAMP'], current_time)
                        status, rms_state = dict['BITRATE_STATE']['PARAMS']
                    if 'RTCP_STATS' in dict:
                        self.rec_bitrate, self.rec_jitter = dict['RTCP_STATS']['PARAMS']
                else:
                    break
        except socket.timeout:
            print("Timeout!, Marking status as degraded")
            status = str(Status.Degraded)
        
        return status, rms_state
    
    def parse_status(self):
        status, rms_state = self.get_status()
        print("Received Status: %s" % status)

        if status == str(Status.Progressive):
            #Increase bitrate and framerate
            self.params.change_params(temporal=1, spatial=1)
        elif status == str(Status.Stable):
            #TODO Increase temporal resolution
            self.params.change_params(temporal=1, spatial=0)
        elif status == str(Status.Fluctuated):
            #TODO do nothing
            pass
        elif status == str(Status.Degraded):
            # reduce both spatial and temporal res
            self.params.change_params(temporal=-1, spatial=-1)
        else:
            # # Wait for next feedback to make change
            # pass
            # Check rms state
            if rms_state == 1: # decreasing rms
                self.params.change_params(temporal=0, spatial=-1)
            elif rms_state == 0: # increasing rms
                self.params.change_params(temporal=0, spatial=1)
        
        return

    def set_bitrate(self, videosrc, videocaps):

        self.parse_status()

        framerate = self.params.get_temporal_res()
        self.update_framerate(framerate)

        self.bitrate = self.params.get_spatial_res()
        # logging.debug(self.caps)
        # logging.debug(videocaps.get_property("caps").to_string())
        videocaps.set_property("caps", Gst.Caps.from_string(self.caps))

        # logging.debug(videosrc.set_caps())
        
        logging.debug("Updating video bitrate to {0}".format(self.bitrate))
        videosrc.set_property("bitrate", self.bitrate)
        videosrc.set_property("annotation-text", 
        "Sender Bitrate %d Framerate %d  Receiver Bitrate %s Jitter %s  " % 
            (self.bitrate, framerate, self.rec_bitrate, self.rec_jitter))
        return True



    def launch(self):
        hostip = self.conf['host']['stream_hostname']
        hostport = self.conf['host']['stream_rec_port']
        fec = self.conf['pi']['fec_percentage']

        pipeline = Gst.parse_launch(f'\
        rpicamsrc preview=false rotation=180 annotation-mode=time+date+custom-text+black-background name=src \
        bitrate={self.bitrate} annotation-text=\"Bitrate {self.bitrate} \" \
        ! capsfilter caps={self.caps} name=caps \
        ! h264parse \
        ! queue \
        ! rtspclientsink debug=false protocols=udp-mcast+udp \
        location=rtsp://{hostip}:{hostport}/test latency=0 ulpfec-percentage={fec}')

        if pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        videosrc = pipeline.get_by_name("src")
        videocaps = pipeline.get_by_name("caps")

        GLib.timeout_add(5000, self.set_bitrate, videosrc, videocaps)

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
