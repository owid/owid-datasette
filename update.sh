#!/bin/bash -e
# This script rebuilds the sqlite file and restarts the datasette systemd service
git pull
./sqlite-from-mysql.sh
sudo systemctl restart datasette