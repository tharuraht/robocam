# robocam

This repository contains the system implementation of the 'Design and Implementation of a Remote-Controlled Robot Platform connected to 4G' MEng project conducted with the department of Electrical Engineering at Imperial College London.

## Abstract

With the ever-growing importance and utilization of robotics in every-day actions, and the significant increase in the performance of mobile data networks. This project collates research regarding the performance of current mobile networks (in particular 4G), frameworks to enable
low-latency real-time video streaming via 4G, and current ‘off-the-shelf’ components to build a
remote-controlled robot platform.
This research was combined with an iterative design and build process to create a functional remote
platform, capable of communicating and being controlled by a host machine via a mobile network
connection, and providing a live video stream with sub-second latency from the on-board camera.
The system is designed to automatically setup and connect on startup, with various contingencies
researched and implemented to improve the robustness of the system.

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

## Configuration

The system can be configured in various ways via the [`robocam_conf.json`](robocam.json) file, with descriptions given in [`CONFIG_DESC.md`](CONFIG_DESC.md).

## Starting the System

Each node has a central run command:

- Host Machine: `host_setup.sh`
- RPi: `pi_setup.sh`

Simply run these commands manually, or configure the OS to run them automatically on startup (e.g. via crontab)
