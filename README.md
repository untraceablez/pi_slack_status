# Pi Slack Status

## Intro

This is a simple Python-based app for displaying your Slack status fullscreen on a Raspberry Pi. I designed the app around the display I'm [using](https://www.microcenter.com/product/632693/inland-35-inch-tft-lcd-touch-screen-monitor) but you can adjust the code to use whatever display output you need. 

## Dependencies & Setup

### Hardware Requirements
* A Raspberry Pi. (Any model that can run Python 3 should work, but as a warning, this was only tested on a Raspberry Pi 5.)
* A hardware display. 
  
### Setup

1. Run updates on your Pi `sudo apt-get update -y && sudo apt-get full-upgrade -y`
2. Install any necessary drivers for your display. 
   1. If you're using the same display I used, use the `LCD35-show` driver from [this repository](https://github.com/goodtft/LCD-show).
   2. Make sure to enable I2C or SPI via `sudo raspi-config` > Interface Options if needed. Refer to your hardware documentation to find out.
3. Install the needed dependencies by running `sudo apt-get install python3-full python3-pip git`. 
4. Clone this repository: `git clone https://github.com/untraceablez/pi_slack_status` and then `cd pi_slack_status`.
5. Create a Python virtual environment named *.venv* using this command: `python3 -m venv .venv`
6. Run `source .venv/bin/activate`. 
7. Run `pip install -r requirements.txt` to install the various Python dependencies.
8. 