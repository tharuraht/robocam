#!/usr/bin/python3
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import rec_bitrate
import json

#hostname = '10.200.200.1'
hostname = '0.0.0.0'

class video_receiver:
    # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    rec_bitrate = 0
    stream_started = False

    def __init__(self):
        with open("robocam_conf.json") as conf_file:
            self.conf = json.load(conf_file)

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
            self.stream_started = True
        return True

    def update_bitrate(self, pipeline):
        self.rec_bitrate = rec_bitrate.get_bitrate(time=1)
        tcp_ip = self.conf['pi']['vpn_addr']
        tcp_port = self.conf['pi']['comms_port']
        if self.stream_started:
            print(f"connecting to {tcp_ip} {tcp_port}")
            rec_bitrate.send_bitrate(tcp_ip, tcp_port, self.rec_bitrate)
        print('Update finished')
        return False

    def launch(self):
        pipeline = Gst.parse_launch(f"\
        tcpserversrc port=5000 host={hostname} name=src \
        ! gdpdepay \
        ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink sync=false")

        if pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        GLib.timeout_add(5000, self.update_bitrate, pipeline)

        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        # cleanup
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    rec = video_receiver()
    rec.launch()

