#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import Gst, GLib, GstBase, GObject, GstRtspServer, Gio, GstRtsp
import json
import ctypes
import logging
import os

try:
    x11 = ctypes.cdll.LoadLibrary('libX11.so')
    x11.XInitThreads()
except:
    logging.warning("Warning: failed to XInitThreads()")

Gst.init(None)
Gst.debug_set_active(True)
# Gst.debug_set_default_threshold(3)

class RTSP_Factory(GstRtspServer.RTSPMediaFactory):
    """
    RTSPMediaFactory override to keep notion of own pipeline
    """
    pipeline = None
    def __init__(self, pipeline_desc):
        GstRtspServer.RTSPMediaFactory.__init__(self)
        self.set_transport_mode(GstRtspServer.RTSPTransportMode.RECORD)
        self.pipeline_desc = pipeline_desc

    def do_create_element(self, url):
        self.pipeline = Gst.parse_launch(self.pipeline_desc)
        logging.debug("Using overriden pipeline creation")
        return self.pipeline

class RTSP_Server:
    port = "5000"
    mount_point = "/test"
    latency = 100
    conf = None
    factory = None
    server =  None
    ctrl_q = None # Receiver control listening queue

    def __init__(self,conf, ctrl_rec_q = None):
        self.conf = conf
        self.ctrl_q = ctrl_rec_q
        logging.basicConfig(filename=conf['log_path'], filemode='a',
        format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
        logging.getLogger().addHandler(logging.StreamHandler())

  # def probe_callback(self,pad,info): 
  #     dts = info.get_buffer().dts
  #     pts = info.get_buffer().pts
  #     print("PTS",pts,"DTS",dts)
  #     print(dir(info.get_buffer()))
  #     print(info.get_buffer().get_reference_timestamp_meta())
  #     print(info.get_buffer().get_meta())
  #     return Gst.PadProbeReturn.DROP

    def get_pipeline(self):
        save_dir = self.conf["host"]["video_dir"]
        if not os.path.exists(save_dir):
            logging.warning("Save directory doesn't exist, using default...")
            os.mkdir("/tmp/robocam_video/")
            save_dir = "/tmp/robocam_video/"

        duration = self.conf["host"]["video_save_dur"]
        logging.debug("Saving to %s" % save_dir)


        primary_cam = f'\
        rtph264depay name=depay1\
        ! queue \
        ! h264parse config-interval=1 name=parse \
        ! tee name=filesave \
        ! queue \
        ! avdec_h264 \
        ! clockoverlay halignment=left valignment=bottom \
        text="Current Time" shaded-background=true font-desc="Sans, 11" \
        ! timeoverlayparse \
        ! videoconvert \
        ! queue \
        ! autovideosink sync=false\
        '
        
        filesink = f'\
        filesave. \
        ! queue leaky=2 \
        ! multifilesink location={save_dir}/host_video%02d.mov \
            max-file-duration={duration}\
        '

        secondary_cam = '\
        rtph264depay name=depay0 \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink sync=false\
        '
        pipeline = primary_cam + secondary_cam + filesink
        return pipeline
    

    def on_ssrc_active(self, session, source):
        stats = source.get_property("stats")
        is_sender = stats.get_boolean("is-sender")
        # print(is_sender)
        if is_sender[1]:
            bitrate = stats.get_uint64("bitrate")
            jitter = stats.get_uint("jitter")
            # print(bitrate[1],jitter[1])
            data = f"{bitrate[1]},{jitter[1]}"
            with open("tmp/rec_stats.tmp","w") as f:
                f.write(data)
            
            # twcc_stats = source.get_property("twcc-stats")
            # print("TWCC stats:",twcc_stats)


    def media_prepared_cb(self, media):
        n_streams = media.n_streams()
        logging.debug("Media %s is prepared and has %0d streams" % (media, n_streams))

        for i in range(n_streams):
            stream = media.get_stream(i)

        if stream is None:
            logging.debug("No stream present")
            return
        
        session = stream.get_rtpsession()
        logging.debug("Watching session %s on stream %0d" % (session,i))

        # print(dir(stream))
        # rtcp_range = stream.get_server_port(Gio.SocketFamily.IPV4)
        # print("rtcp ports", rtcp_range.to_string(GstRtsp.RTSPTimeRange))
        # print("rtp socket", stream.get_rtp_socket(Gio.SocketFamily.IPV4))
        
        # Add probe: https://github.com/vk-gst/Probes-handling-in-GStreamer-pipelines
        # get the element handle from pipeline
        # pipeline = self.factory.pipeline
        # print(pipeline)
        # src_element = pipeline.get_by_name('depay0')
        # #get the static source pad of the element
        # srcpad = src_element.get_static_pad('src')
        # #add the probe to the pad obtained in previous solution
        # probeID = srcpad.add_probe(Gst.PadProbeType.BUFFER, self.probe_callback)

        # Workaround camera PTS issue
        # https://stackoverflow.com/questions/42874691/gstreamer-for-android-buffer-has-no-pts
        parse = self.factory.pipeline.get_by_name("parse")
        GstBase.BaseParse.set_infer_ts(parse, True)
        GstBase.BaseParse.set_pts_interpolation(parse, True)

        session.connect("on-ssrc-active", self.on_ssrc_active)


    def media_configure_cb(self, factory, media):
        media.connect("prepared", self.media_prepared_cb)

  
    def create_server(self):
        self.server = GstRtspServer.RTSPServer.new()
        self.server.set_service(self.port)
        mounts = self.server.get_mount_points()
        factory = RTSP_Factory(self.get_pipeline())
        factory.set_latency(self.latency)

        #Callback to start tracing once media is prepared for streaming
        factory.connect("media-configure", self.media_configure_cb)

        self.factory = factory

        # Dont reference factory after this point
        mounts.add_factory(self.mount_point, factory)
        self.server.attach()
        #  start serving
        logging.info("stream ready at rtsp://127.0.0.1:" + self.port + "/test");

    def parse_commands(self, command):
        pass


    def get_commands(self):
        if self.ctrl_q is not None:
            # print("Parsing commands from queue")
            if not self.ctrl_q.empty():
                command = self.ctrl_q.get(False)
                logging.debug("Command received:", command)
                self.parse_commands(command)
        else:
            logging.warning("No control queue set")
        return True


    def launch(self):
        self.create_server()

        GLib.timeout_add(50, self.get_commands)

        loop = GLib.MainLoop()
        loop.run()

if __name__ == '__main__':
    with open('robocam_conf.json') as f:
        conf = json.load(f)
    server = RTSP_Server(conf)
    server.launch()