
# Setup

## Libraries and Prerequisites

### GStreamer

Requires `GStreamer 1.18+`, which can be installed via [gst-build](https://gstreamer.freedesktop.org/documentation/installing/building-from-source-using-meson.html?gi-language=c). The summary of installation steps are as follows, and should be performed on both nodes:

- Install git and python 3.5+
- Install meson and ninja (both should be available via a pacakage manager e.g. `apt`)
- Clone the [gst-build directory](https://github.com/GStreamer/gst-build)
- Enter cloned directory and run `meson <build_dir>` (on the RPi run `meson <build_dir> -D omx=enabled -D gst-omx:target=rpi`) where build_dir can be any directory except the gst-build directory (it can be inside the directory however). e.g. the RPi in the original project used 'build', which created the build directory inside the gst-build directory.
- Once `meson` is done, enter the build_dir and run `ninja `. This will compile all modules
- As a quick check, enter the environment by running `ninja -C <build_dir> devenv` and run `gst-inspect-1.0 --version`

Once the environment is installed, the `gst_path` field in `robocam_conf.json` must be set accordingly to find the `gst-env.py` file found in the directory.

### (Optional) Latency-Clock

The [latency-clock](https://github.com/tharuraht/latency-clock) is a fork from the main [repo](https://github.com/stb-tester/latency-clock), and was intended to be used to gather automatic latency statistics regarding the video stream, for later analysis or even to create an alternative adaptive bitrate algorithm for the video streamer. However, due to a bug this could not be used (see project dissertation for details).

### Python Libraries

The following libraries are all Python3 compatible libraries, and can be installed via `pip3 install <name>`

- pygame
- psutil
- ipstack
- miniupnpc
- matplotlib
- speedtest-cli

### Other prerequisites

- [Wireguard VPN](https://www.wireguard.com/install/)
- [Arduino IDE](https://www.arduino.cc/en/software)

## Setup Instructions

### Wireguard VPN

The Wireguard VPN tunnel between the two nodes is based on the instructions listed [here](https://www.ckn.io/blog/2017/11/14/wireguard-vpn-typical-setup/). The basic steps are summarised as follows:

1. Install Wireguard on both nodes (available on most package managers).

  ```
  add-apt-repository ppa:wireguard/wireguard
  apt-get update
  apt-get install wireguard-dkms wireguard-tools linux-headers-$(uname -r)
  ```

2. Generate server and client keys (should generate four files in total)

  ```
  Umask 077
  wg genkey | tee server_private_key | wg pubkey > server_public_key
  wg genkey | tee client_private_key | wg pubkey > client_public_key
  ```

3. Update Wireguard server and client files (found in this repository at `utils/wireguard/`) with generated keys, copy the corresponding file to `/etc/wireguard/` in each node:

  - Use the server config [`wg0.conf`](utils/wireguard/wg0.conf) for the host machine
  - Use the client config [`wg0-client.conf`](utils/wireguard/wg0-client.conf) for the RPi

4. Enable Wireguard server interface (can confirm by running the `ifconfig` command and checking for the 'wg0' interface)

  ```
  chown -v root:root /etc/wireguard/wg0.conf
  chmod -v 600 /etc/wireguard/wg0.conf
  wg-quick up wg0
  systemctl enable wg-quick@wg0.service #Enable the interface at boot
  ```

5. Setup Wireguard on client (RPi).

  ```
  sudo systemctl enable wg-quick@wg0-client.service
  ```

  - You can manually enable the tunnel via `sudo wg-quick up wg0-client`
  - To manually disable the tunnel, use `sudo wg-quick down wg0-client`
  - To view connection status, use `sudo wg show`
  - You can quickly test the connection using `ping`
    - Server (host machine) address: 10.200.200.1
    - Client (RPi) address: 10.200.200.2


### Wireguard watchdog

Found in `utils/wg-watchdog.sh`, the script periodically checks if the VPN tunnel is active and will attempt to restart it if not.
Can be run manually or configured to peridically run using `crontab`, the crontab entry used in the original project on the RPi was given as:

```
*/15 * * * * /home/pi/Documents/robocam/utils/wg-watchdog.sh
```

### Arduino Code

The arduino code is located at `robot/ser_car/ser_car.ino`. It can be compiled and uploaded to the Arduino via the Arduino IDE.

### ipstack

The location estimation feature of the system uses [ipstack geolocation API](https://ipstack.com/), which requires a personal key to be obtained (free with a signup). Once key is obtained, replace `ipstack.key` contents with key or a create symbolic link to a file containing the key.