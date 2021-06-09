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
        [sg.Text("RPi Status")],
        [sg.Text("Connection Status: Disconnected", key="-RPI STATUS-")],
        [sg.Listbox(values=[], enable_events=True, size=(40,20), key="-STAT LIST-")],
    ]

    host_log = [
        [sg.Text("Host Machine Log")],
        [sg.Listbox(values=[], enable_events=True, size=(100,50), key="-HOST LOG-")]
    ]

    pi_log = [
        [sg.Text("RPi Log")],
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

    window = sg.Window("System Status", layout)

    def __init__(self, conf):
        self.conf = conf
    
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

    
    def rpi_status_update(self):
        addr = self.conf['pi']['vpn_addr']
        # port = self.conf['pi']['comms_port']
        port = 5010
        buff_sz = 500
        status = []

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        connection = "Disconnected"

        try:
            sock.connect((addr,port))
            while True:
                data = sock.recv(buff_sz)
                if data:
                    msg = data.decode('utf-8')
                    # print(msg)
                    msg_dict = json.loads(msg)
                    status = pretty_string(msg_dict)
                    connection = "Connected"
                else:
                    break
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

            # Update host machine log
            self.host_log_update()

            # Update rpi status
            self.rpi_status_update()

            self.rpi_log_update()

        self.window.close()

if __name__ == '__main__':
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)
    s = Sys_Stats(conf)
    s.event_loop()