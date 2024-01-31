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

# NOTE: it's not yet clear whether it'd be more useful to have metadata.yml in the analytics repository close to
#   actual tables or in the owid-datasette repository close to Datasette. For now we'll keep it in the analytics
# Copy metadata.yml from analytics repository
# (
#     cd /home/owid
#     git clone git@github.com:owid/analytics.git || true
#     cd analytics
#     git pull
#     cp snail/metadata.yml /home/owid/owid-datasette/metadata.yml
# )

git pull
git commit --allow-empty -m "Nightly rebuild"
git push
sudo systemctl restart datasette
