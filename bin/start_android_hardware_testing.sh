#!/bin/bash

. /etc/bitbar/bitbar.env
. /home/bitbar/mozilla-bitbar-devicepool/venv/bin/activate
export PYTHONPATH=/home/bitbar/mozilla-bitbar-devicepool
python /home/bitbar/mozilla-bitbar-devicepool/mozilla_bitbar_devicepool/main.py start-test-run-manager --delete-bitbar-tests

