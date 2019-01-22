#!/bin/bash

. /etc/bitbar/bitbar.env
. /home/bitbar/venv/bin/activate
export PYTHONPATH=/home/bitbar
python /home/bitbar/mozilla_bitbar_devicepool/main.py start-test-run-manager --delete-bitbar-tests

