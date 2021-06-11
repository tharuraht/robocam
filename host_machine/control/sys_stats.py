import tkinter
import PySimpleGUI as sg
import json
import socket
import logging
import time
import pprint


# https://realpython.com/pysimplegui-python/

def pretty_string(d, indent=0):
    string_lst = []
    for key, value in d.items():
        if isinstance(value, dict):
            string_lst.append('    ' * indent + str(key) + " : ")
            string_lst += pretty_string(value, indent+1)
        else:
            string_lst.append('    ' * indent + str(key) + " : " + str(value))
    return string_lst


class Sys_Stats():
    stats_column = [
        [sg.Text("RPi Status", font=("Helvetica", 25))],
        [sg.Text("Connection Status: Disconnected", key="-RPI STATUS-", font=("Helvetica", 15))],
        [sg.Listbox(values=[], enable_events=True, size=(40,20), key="-STAT LIST-")],
    ]

    host_log = [
        [sg.Text("Host Machine Log", font=("Helvetica", 20))],
        [sg.Listbox(values=[], enable_events=True, size=(100,50), key="-HOST LOG-")]
    ]

    pi_log = [
        [
            sg.Text("RPi Log", font=("Helvetica", 20)),
            sg.Button("Refresh")
        ],
        [sg.Listbox(values=[], enable_events=True, size=(100,50), key="-RPI LOG-")]
    ]

    layout = [
        [
            sg.Column(stats_column),
            sg.VSeperator(),
            sg.Column(host_log),
            sg.VSeperator(),
            sg.Column(pi_log),
        ]
    ]

    window = sg.Window("System Stats", layout)

    def __init__(self, conf):
        self.conf = conf
        logging.basicConfig(filename=conf['log_path'], filemode='a',
        format=conf['log_format'], level=logging.getLevelName(conf['log_level']))
    
    def __del__(self):
        self.window.close()

    def host_log_update(self):
        try:
            with open(self.conf['log_path'], 'r') as f:
                lines = f.readlines()
                lines = lines[-50:]
                lines = [line.strip() for line in lines]
        except:
            lines = ["Unable to open log file"]
        self.window["-HOST LOG-"].update(lines)
    
    def rpi_log_update(self):
        pass

    
    def rpi_status_update(self, log = False):
        addr = self.conf['pi']['vpn_addr']
        port = self.conf['pi']['comms_port']
        buff_sz = 5000
        status = []

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        connection = "Disconnected"
        msg = "[LOG]" if log else "[NO_LOG]"
        rec_msg = ""
        pi_log = []

        try:
            sock.connect((addr,port))
            sock.sendall(msg.encode())
            while True:
                data = sock.recv(buff_sz)
                if data:
                    rec_msg += data.decode('utf-8')
                    # print(msg)
                else:
                    break
            msg_dict = json.loads(rec_msg)
            pi_log = msg_dict.pop('pi_log')
            status = pretty_string(msg_dict)
            connection = "Connected"
        except socket.timeout:
            connection = "Timeout"
        except socket.error as e:
            # status = ["Socket error: %s (%f)" % (e,time.time()) ]
            connection = "Disconnected - Socket error: %s (%f)" % (e,time.time())
        except Exception as e:
            logging.exception("Unhandled Exception! Exiting... ",e)
            exit(1)
        finally:
            sock.close()
        
        if len(status) > 0:
            self.window["-STAT LIST-"].update(status)

        if len(pi_log) > 0:
            self.window['-RPI LOG-'].update(pi_log)

        self.window['-RPI STATUS-'].update("Connection Status: %s" % connection)

    def event_loop(self):
        while True:
            self.window.refresh()
            event, values = self.window.read(timeout=3000)
            # End program if user closes window or
            # presses the OK button
            if event == "OK" or event == sg.WIN_CLOSED:
                break
            if event is None or event == "Exit":
                break
            if event is not None and event != "__TIMEOUT__":
                logging.debug("GUI Event: %s" % event)

            # Update host machine log
            self.host_log_update()

            # Update rpi status
            self.rpi_status_update(event == "Refresh")

        self.window.close()

if __name__ == '__main__':
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    s = Sys_Stats(conf)
    s.event_loop()