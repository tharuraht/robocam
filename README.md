# robocam

This repository contains the system implementation of the 'Design and Implementation of a Remote-Controlled Robot Platform connected to 4G' MEng project conducted with the department of Electrical Engineering at Imperial College London.

## TODO

- verify if there is a latency difference between profiles, select best one
- find the 'auto' keyframe interval (print it out?)
- possibly add framerate profiles depending on network conditions (e.g. lower framerate, more keyframes)
- change RTSP config to use Secure RTP (see profiles option for rtsp client sink)
- enable username and password for RTSP
- add overlay showing connection information to pi

## Repository Structure

The repository is broken down as follows:

- [`host_machine`](host_machine/README.md): contains the primary software implementation of the system on the host machine
- [`robot`](robot/README.md): contains the primary software implementation of the system on the robot platform (i.e. the Raspberry Pi)
- [`robocam_conf.json`](robocam_conf.json): central configuration file for the system
- [`utils`](utils/README.md): libraries and scripts written to assist the system
- `results`: holds some results and scripts used to obtain results included in the project thesis
- `ipstack.key`: key or symlink to key of the ipstack API
- `host_setup.sh`: script to start  host machine end of system
- `pi_setup.sh`: script to start robot platform end of system
- `old_dev`: previous software written and tested in the iterative design process

Refer to the README files included in each folder for a breakdown of each file.

## Setup

For setup instructions and a list of pre-requisites refer to [SETUP.md](SETUP.md).

## Starting the System

Each node has a central run command:

- Host Machine: `host_setup.sh`
- RPi: `pi_setup.sh`

Simply run these commands manually, or configure the OS to run them automatically on startup (e.g. via crontab)
