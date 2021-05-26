#!/usr/bin/env python3
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
from pijuice import PiJuice


Gst.init(None)
# Gst.debug_set_active(True)
# Gst.debug_set_default_threshold(3)

class Anno_modes(Enum):
    date = 0x00000004
    time = 0x00000008
    custom_text = 0x00000001
    black_bg = 0x00000400

class Video_params:
    temporal_res = [15,25,30,40]
    spatial_res = [100000, 300000, 600000, 1000000, 2000000, 5000000, 7000000, 10000000]

    def __init__(self):
        self.cur_temp_idx = 2
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
    loop = GLib.MainLoop()
    params = Video_params()
    pijuice = PiJuice(1, 0x14) # Instantiate PiJuice interface object
    ctrl_q = None # Comands send from control
    rec_bitrate = rec_jitter = -1
    show_stats = True
    second_cam = False
    # Controls whether to show timestamp overlay for latency calculation
    timestampoverlay = False


    def __init__(self, conf, ctrl_streamer_q = None):
        self.conf = conf
        self.bitrate = conf['pi']['starting_bitrate']
        self.caps = self.conf['pi']['stream_params']
        self.ctrl_q = ctrl_streamer_q

    def get_pipeline_desc(self):
        hostip = self.conf['host']['stream_hostname']
        hostport = self.conf['host']['stream_rec_port']
        fec = self.conf['pi']['fec_percentage']
        rev_cam_params = self.conf['pi']['rev_cam_params']

        
        annotation = Anno_modes.date.value + Anno_modes.time.value + Anno_modes.black_bg.value
        if self.show_stats:
            annotation += Anno_modes.custom_text.value

        overlay = "! timestampoverlay" if self.timestampoverlay else ""

        primary_cam = f'\
        rpicamsrc preview=false rotation=180 annotation-mode={annotation} name=src \
        bitrate={self.bitrate} annotation-text=\"Bitrate {self.bitrate} \" \
        ! capsfilter caps={self.caps} name=caps \
        ! h264parse \
        ! queue name=pay0 \
        ! rtsp. \
        '

            # ! textoverlay text="Reverse Camera: Disabled" valignment=top halignment=centre font-desc="Sans, 11" \
        if self.second_cam:
            cam_src = "v4l2src device=/dev/video0"
        else:
            cam_src = 'videotestsrc is-live=True pattern=black num-buffers=1 \
            ! omxh264enc'
        
        rev_cam = f'\
        {cam_src} \
        ! {rev_cam_params} \
        ! h264parse name=pay1 \
        ! rtsp. \
        '

        rtsp_client = f'\
        rtspclientsink debug=false protocols=udp-mcast+udp name=rtsp \
        location=rtsp://{hostip}:{hostport}/test latency=0 ulpfec-percentage={fec} \
        '

        desc = primary_cam + rtsp_client + rev_cam

        return desc


    def bus_call(self, bus, msg, *args):
        # print("BUSCALL", msg, msg.type, *args)
        if msg.type == Gst.MessageType.EOS:
            logging.info("End-of-stream")
            self.loop.quit()
            return
        elif msg.type == Gst.MessageType.ERROR:
            logging.error(f"GST ERROR {msg.parse_error()}")
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
        s.settimeout(0.5)

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
        except socket.error as e:
            print("Socket error %s, passing..." % e)
        except Exception as e:
            print("Unhandled Exception! Exiting... ",e)
            exit(1)
        
        return status, rms_state
    
    def parse_status(self):
        status, rms_state = self.get_status()
        print("Received Status: %s, RMS: %0d" % (status, rms_state))

        # TODO restore temporal changes

        if status == str(Status.Progressive):
            self.params.change_params(temporal=0, spatial=1)
        elif status == str(Status.Stable):
            self.params.change_params(temporal=0, spatial=0)
        elif status == str(Status.Fluctuated):
            self.params.change_params(temporal=0, spatial=0)
        elif status == str(Status.Degraded):
            # reduce both spatial and temporal res
            # self.params.change_params(temporal=-1, spatial=-1)
            self.params.change_params(temporal=0, spatial=-1)
        else:
            # # Wait for next feedback to make change
            # pass
            # Check rms state
            if rms_state == 1: # decreasing rms
                self.params.change_params(temporal=0, spatial=-1)
            elif rms_state == 0: # increasing rms
                self.params.change_params(temporal=0, spatial=1)
            elif int(self.rec_bitrate) > self.bitrate: #TODO trying it out
                self.params.change_params(temporal=0, spatial=1)
        
        return
    
    def update_annotation(self):
        framerate = self.params.get_temporal_res()
        videosrc = self.pipeline.get_by_name("src")

        bat_lvl = self.pijuice.status.GetChargeLevel()['data'] # Get battery level
        charge_stat = self.pijuice.status.GetStatus()['data']['powerInput']

        rev_cam_status = "On" if self.second_cam else "Off"

        annotation = ("Sender Bitrate %d Framerate %d  Receiver Bitrate %s \
        Jitter %s Rev Camera: %s \nBattery: %0d%% External Power: %s   " %
            (self.bitrate, framerate, self.rec_bitrate, self.rec_jitter, rev_cam_status, bat_lvl, charge_stat))


        videosrc.set_property("annotation-text", annotation)
        return True

    def set_bitrate(self):
        videosrc = self.pipeline.get_by_name("src")
        videocaps = self.pipeline.get_by_name("caps")
        self.parse_status()

        framerate = self.params.get_temporal_res()
        self.update_framerate(framerate)

        self.bitrate = self.params.get_spatial_res()
        # logging.debug(self.caps)
        # logging.debug(videocaps.get_property("caps").to_string())
        # videocaps.set_property("caps", Gst.Caps.from_string(self.caps))
        # logging.debug(videosrc.set_caps())
        logging.debug("Updating video bitrate to {0}".format(self.bitrate))
        videosrc.set_property("bitrate", self.bitrate)
        return True

    def restart(self):
        print("RESTARTING")
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        # self.pipeline.set_state(Gst.State.NULL)
        # time.sleep(1)
        # self.pipeline = Gst.parse_launch(self.get_pipeline_desc())
        # time.sleep(1)

        # bus = self.pipeline.get_bus()
        # bus.add_watch(0, self.bus_call, self.loop)


        self.pipeline.set_state(Gst.State.PLAYING)
        return True

    def parse_commands(self, command):
        #TODO parse commands
        if command == "[TOGGLE_STATS]":
            self.show_stats = not self.show_stats
            annotation = Anno_modes.date.value + Anno_modes.time.value + Anno_modes.black_bg.value
            if self.show_stats:
                annotation += Anno_modes.custom_text.value
            print("Show stats:",self.show_stats)
            videosrc = self.pipeline.get_by_name("src")
            videosrc.set_property("annotation-mode", annotation)
        elif command == "[INC_FPS]":
            self.params.change_params(temporal=1)
            framerate = self.params.get_temporal_res()
            self.update_framerate(framerate)
            self.restart()
        elif command == "[DEC_FPS]":
            self.params.change_params(temporal=-1)
            framerate = self.params.get_temporal_res()
            self.update_framerate(framerate)
            self.restart()
        elif command == "[PIPE_RESTART]":
            self.restart()
        elif command == "[TOGGLE_SEC_CAM]":
            print("Toggling second camera from %s" % self.second_cam)
            self.second_cam = not self.second_cam
            self.restart()


    def get_commands(self):
        if self.ctrl_q is not None:
            # print("Parsing commands from queue")
            while not self.ctrl_q.empty():
                command = self.ctrl_q.get(False)
                print("Command received:", command)
                self.parse_commands(command)
        else:
            print("No control queue set")
        return True


    def launch(self):
        print("Launching stream")
        self.pipeline = Gst.parse_launch(self.get_pipeline_desc())

        if self.pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = self.pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        # Functions below are periodically called
        GLib.timeout_add_seconds(5, self.set_bitrate)
        GLib.timeout_add(50, self.get_commands)
        GLib.timeout_add(500, self.update_annotation)

        # run
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        finally:
            # cleanup
            self.pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    
    # Configure Logger TODO change to use conf
    logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s', \
        level=logging.getLevelName(conf['log_level']))

    streamer = video_streamer(conf)
    streamer.launch()
