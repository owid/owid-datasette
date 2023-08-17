#!/bin/bash -e
# This script rebuilds the sqlite file, triggers empty commit and restarts the datasette systemd service
git pull
./sqlite-from-mysql.sh
git pull
git commit --allow-empty -m "Nightly rebuild"
git push
sudo systemctl restart datasette
