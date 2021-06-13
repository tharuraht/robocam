# Host Machine Software

This folder contains software used in the host machine portion of the system:

- control: software to control aspects of RPi and collect statistics
  - [`robot_control.py`](control/robot_control.py): connected to joystick, parses inputs into a JSON string and sends to RPi via network.
  - [`sys_stats.py`](control/sys_stats.py): generates a GUI, showing RPi statistics and logs from both nodes of the system.
- rtsp_src: software related to the RTSP stream receiver
  - [`ps_bitrate.py`](rtsp_rec/ps_bitrate.py): continuously polls the OS to calculate the receiving bitrate within small windows. On request, will analyse and classify the bitrate pattern (algorithm referenced in report).
  - [`rtsp_server.py`](rtsp_rec/rtsp_server.py): RTSP server to listen for RTSP streaming clients.
  - [`upnp_rtsp.py`](rtsp_rec/upnp_rtsp.py): handles port forwarding of ports opened by the RTSP as it handshakes with clients.
- [`start.py`](start.py): Host machine process manager, additional processes needed to run in parallel are added here.
