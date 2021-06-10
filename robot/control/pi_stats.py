from ipstack import GeoLookup
from gpiozero import CPUTemperature
import psutil
from pijuice import PiJuice
import socket
import json

class Pi_Stats():
    def __init__(self, conf):
        with open("ipstack.key") as f:
            key = f.read()
        self.conf = conf
        self.geo_lookup = GeoLookup(key)

        self.pijuice = PiJuice(1, 0x14) # Instantiate PiJuice interface object

    def main_loop(self):
        port = self.conf['pi']['comms_port']
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('',port))
        s.listen()
        print("Listening on port %0d" % port)

        while True:
            try:
                # print("Waiting")
                conn, addr = s.accept()
                print("Connected")
                data = conn.recv(16)
                if addr[0] == self.conf['host']['vpn_addr']:
                    info_dict = self.generate_info(data.decode('utf-8'))
                    dump = json.dumps(info_dict)
                    print(dump)
                    conn.sendall(dump.encode())

                else:
                    print("Invalid connecting address", addr)
            finally:
                conn.close()



    def generate_info(self, req):
        info = {}

        lookup = self.ip_lookup()
        if lookup is not None:
            keys = ['ip', 'continent_code', 'country_code', 'region_code', 'city', 'zip', 'latitude', 'longitude']
            info['ip_info'] = {key:lookup[key] for key in keys}

        cpu_temp = CPUTemperature().temperature
        cpu_load = psutil.cpu_percent()
        mem_load = psutil.virtual_memory().percent
        info['cpu_status'] = {
            'temperature': f"{cpu_temp}"+u"\N{DEGREE SIGN}"+"C",
            'load' : f"{cpu_load}%",
            'mem_load' : f"{mem_load}%"
        }

        bat_lvl = self.pijuice.status.GetChargeLevel()['data'] # Get battery level
        charge_stat = self.pijuice.status.GetStatus()['data']['powerInput']
        info['pijuice_status'] = {
            'battery_lvl' : bat_lvl,
            'charge_status' : charge_stat
        }

        info['pi_log'] = []
        if req == "[LOG]":
            with open(self.conf['log_path'], 'r') as f:
                lines = f.readlines()
                lines = lines[-50:]
                lines = [line.strip() for line in lines]
                info['pi_log'] = lines

        return info


    def ip_lookup(self):
        try:
            location = self.geo_lookup.get_own_location()

            if location is None:
                print("Failed to find location")
            return location


        except Exception as e:
            print(e)

if __name__ == '__main__':
    with open("robocam_conf.json") as conf_file:
        conf = json.load(conf_file)

    # while True:
        # time.sleep(5)
    pistats = Pi_Stats(conf)
    info = pistats.main_loop()
    print(info)
