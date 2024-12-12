#!/bin/bash
clear
echo This will use SUDO to update and upgrade apt, as well as to install the python veritual environment
sudo apt upgrade
sudo apt update
sudo apt install -y python3-pip python3-virtualenv
virtualenv venv
./dependencies.sh

