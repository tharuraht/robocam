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
        hostport = self.conf['host']['stream_rec_port']
        self.pipeline = Gst.parse_launch(f"\
        udpsrc port={hostport} name=src \
        ! gdpdepay \
        ! rtph264depay \
        ! avdec_h264 \
        ! videoconvert \
        ! autovideosink sync=false")

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
        self.rec_bitrate = rec_bitrate.get_bitrate(time=2)
        tcp_ip = self.conf['pi']['vpn_addr']
        tcp_port = self.conf['pi']['comms_port']
        if self.stream_started:
            print(f"connecting to {tcp_ip} {tcp_port}")
            rec_bitrate.send_bitrate(tcp_ip, tcp_port, self.rec_bitrate)
        # print('Update finished')
        return True

    def launch(self):
        print("Started GStreamer Receiver")
        if self.pipeline == None:
            print ("Failed to create pipeline")
            sys.exit(0)

        # watch for messages on the pipeline's bus (note that this will only
        # work like this when a GLib main loop is running)
        bus = self.pipeline.get_bus()
        bus.add_watch(0, self.bus_call, self.loop)

        # GLib.timeout_add(5000, self.update_bitrate, pipeline)

        # run
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            self.loop.run()
        except Exception as e:
            print('Caught', e) 
        self.cleanup()
    
    def cleanup(self):
        # cleanup
        self.pipeline.set_state(Gst.State.NULL)

class bitrate_calc:
    def __init__(self, conf):
        self.conf = conf
        self.run_comms_loop = True


    def launch(self):
        tcp_port = self.conf['host']['comms_port']

        print(f'Hosting server on port {tcp_port}')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(1.0)
        self.s.bind(('', tcp_port))
        self.s.listen()
        print("Server is open to connections")
        self.conn = None


        while self.run_comms_loop:
            try:
                self.conn, addr = self.s.accept()
            except socket.timeout as e:
                continue
            # print("Connection address:", addr)
            if addr[0] == self.conf['pi']['vpn_addr']:
                # Measure bitrate and send to pi
                rate = rec_bitrate.get_bitrate(time=2)
                msg = f"REC_BITRATE:{rate}"
                print('Sending', msg)
                self.conn.sendall(bytearray(msg,'utf-8'))
            else:
                print(f'{addr} is not a valid source address')
            self.conn.close()

        self.s.shutdown(1)
        self.s.close()
    #    except KeyboardInterrupt as k:
    #        if conn is not None:
    #            conn.close()
    #        s.close()
    #        throw(k)
    #    finally:
        # self.cleanup()
    
    def cleanup(self):
        self.run_comms_loop = False
    #     if self.conn is not None:
    #         self.conn.close()
    #     self.s.close()

def launch(obj):
    obj.launch()

if __name__ == "__main__":
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    
    rec = video_receiver(conf)
    calc = bitrate_calc(conf)

    try:
        bitrate_proc = Process(target=calc.launch)
        receiver_proc = Process(target=rec.launch)

        receiver_proc.start()
        bitrate_proc.start()

        #receiver_proc.join()
    except Exception as e:
        print(e)

    print("Cleanup")
    rec.cleanup()
    calc.cleanup()
