# Robot Platform Software

This folder contains the software intended for the robot platform end of the system, and is written to run on the Raspberry Pi 4B:

- control: contains software relating to control and operation of RPi and robot platform
  - [`central_control.py`](control/central_control.py): central control module of RPi, listens for control streams from host machine and forwards messages to appropriate components.
  - [`pi_gps.py`](control/pi_gps.py): contains class to extract GPS information from GPS breakout.
  - [`pi_stats.py`](control/pi_stats.py): collects information regading RPi and optionally system log, forwards to host machine on receipt of request.
  - [`robot_ser_relay.py`](control/robot_ser_relay.py): relays received data from central control to Arduino, also handles control unit specific features, such as rewind.
- rtsp_str: software relating to RTSP Client streamer.
  - [`rtsp_stream.py`](rtsp_str/rtsp_stream.py): connects to host machine RTSP server, and streams video using adaptive bitrate and error correction.
  - [`streamer_utils.py`](rtsp_str/streamer_utils.py): helper functions and classes for the RTSP streamer.
- [`ser_car/ser_car.ino`](ser_car/ser_car.ino): Arduino code to generate PWM signals for motor driver.
- [`start.py`](start.py): RPi Process Manager, additional processes needed to run in parallel are added here.
