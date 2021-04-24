# Stat receiver, listens for sent stats and updates stat file
import socket
import json

with open("robocam_conf.json") as conf_file:
    conf = json.load(conf_file)

port = conf['pi']['comms_port']

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('', port))
print(f"Listening for RTCP Stats on port {port}")

while True:
    data, addr = sock.recvfrom(1024)
    print("received message: %s" % data)
    with open("rec_stats.tmp","w") as f:
        f.write(data)