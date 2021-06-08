# Configuration Description

This document summarises the configuration options available in the [`robocam_conf.json`](robocam.json) configuration file.

## Host

- `stream_rec_port`: port for RTSP Server to listen for new RTSP clients
- `stream_rec_intf`: network interface on which the RTSP Server is listening
  - For VPN method, use 'wg0'
  - For port forward method, use the default network interface (e.g. wlp4s0 or wlan0)
- `stream_hostname`: the hostname for which the RTSP Server is reachable.
- `vpn_addr`: address of host machine within VPN tunnel
- `comms_port`: port on host machine to host bitrate measure TCP server
- `gst_path`: location of host machine GStreamer (gst-build) installation
- `video_dir`: directory to store received footage
- `video_save_dur`: duration in nanoseconds of each recorded footage file
- `open_upnp`: use UPnP client to open required ports for system

## Pi

- `vpn_addr`: address of RPi within VPN tunnel
- `control_port`: port for `central_control` to listen for control messages from host machine
- `comms_port`: port for `pi_stats` to bind to and listen for stat requests
- `stream_params`: initial streaming parameters for primary camera, in the format of [GStreamer caps](https://gstreamer.freedesktop.org/documentation/gstreamer/gstcaps.html?gi-language=c#GstCaps)
- `rev_cam_params`: initial streaming parameters for secondary camera
- `rev_cam_dir`: ID of reverse camera, used to find and access the camera
- `starting_bitrate`: inital primary camera streaming bitrate
- `fec_percentage`: FEC percentage redundancy
- `gst_path` location of RPi GStreamer (gst-build) installation
- `video_dir`: save directory of recorded footage
- `video_save_dur`: duration in nanoseconds of each recorded footage file

## Other/Global

- `log_level`: sets the verbosity level of the Python [`logging`](https://docs.python.org/3/howto/logging.html) library
- `log_format`: sets the logger format
- `controller_config`: maps features to keys in the controller hash table sent from the host machine to RPi
