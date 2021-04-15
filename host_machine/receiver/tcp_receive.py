#!/usr/bin/python3
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import rec_bitrate
import json
from multiprocessing import Process
import socket

#hostname = '10.200.200.1'
hostname = '0.0.0.0'

class video_receiver:
    # initialization
    loop = GLib.MainLoop()
    Gst.init(None)
    rec_bitrate = 0
    stream_started = False

    def __init__(self, conf):
        self.conf = conf

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
        # print('Update finished')
        return True

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

        # GLib.timeout_add(5000, self.update_bitrate, pipeline)

        # run
        pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print(e)
        # cleanup
        pipeline.set_state(Gst.State.NULL)

def calculate_bitrate(conf):
    tcp_port = conf['host']['comms_port']

    print(f'Hosting server on port {tcp_port}')

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', tcp_port))
    s.listen()
    print("Server is open to connections")
    while True:
        try:
            conn, addr = s.accept()
            # print("Connection address:", addr)
            if addr[0] == conf['pi']['vpn_addr']:
                # Measure bitrate and send to pi
                rec_bitrate = rec_bitrate.get_bitrate(time=2)
                msg = f"REC_BITRATE:{rec_bitrate}"
                conn.sendall(bytearray(msg,'utf-8'))
            else:
                print(f'{addr} is not a valid source address')
        finally:
            conn.close()



if __name__ == "__main__":
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    
    rec = video_receiver(conf)
    bitrate_proc = Process(target=calculate_bitrate, args=(conf,))
    bitrate_proc.start()

    receiver_proc = Process(target=rec.launch())
    receiver_proc.start()

    receiver_proc.join()
    bitrate_proc.terminate()
