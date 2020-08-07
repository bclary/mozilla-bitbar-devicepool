#!/bin/bash

pkill -USR2 -f main.py
while pkill -0 -f main.py; do
    sleep 1
done
