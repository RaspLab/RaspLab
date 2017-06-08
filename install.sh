#!/bin/bash
git clone https://github.com/RaspLab/RaspLab.git
pip3 install -r RaspLab/requirements.txt
echo "@python3 $(pwd)/RaspLab/python/RaspLab.py">> .config/lxsession/LXDE-pi/autostart
reboot
