#!/bin/bash
clear
echo Clearning Logs
rm ./logs/*.log

echo Activating Python virtual environment
source venv/bin/activate

echo Executing
python ssp_content_creator.py
