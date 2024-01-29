#!/bin/bash -e
# This script fetches SQLite databases, triggers empty commit and restarts the datasette systemd service

# Rename generated SQLite database to owid.db for backwards compatibility
s3cmd cp s3://owid-public/owid-public.sqlite.gz s3://owid-public/owid.db.gz

# Fetch private database
# NOTE: one-liner doesn't work for some reason
# s3cmd get s3://owid/owid-private.sqlite.gz - | gunzip > owid.db
s3cmd get s3://owid/owid-private.sqlite.gz
gunzip owid-private.sqlite.gz
mv owid-private.sqlite owid.db

git pull
git commit --allow-empty -m "Nightly rebuild"
git push
sudo systemctl restart datasette
