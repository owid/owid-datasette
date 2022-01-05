#!/usr/bin/env  bash
set -o errexit
set -o pipefail
set -o nounset

# Remove the old file if there is one
rm owid.db || true
# Run mysqldump with a subset of tables and some flats to bring it into the required format, the
# pipe this into mysql2sqlite and pipe this into sqlite3 to created owid.db
mysqldump --skip-extended-insert --column-statistics=0 --compact --port \
    $DB_PORT --password=$DB_PASSWD --user $DB_USER --host $DB_HOST $DB_NAME \
    users variables tags sources posts post_tags namespaces datasets dataset_tags charts chart_tags chart_slug_redirects \
  | ./mysql2sqlite - \
  | sqlite3 owid.db
# Run the postprocess-db python script. This is the place to censor some rows or add views etc
python postprocess-db.py
# Gzip the file
gzip -9 -c owid.db > owid.db.gz
# And upload to s3
s3cmd put owid.db.gz s3://owid