#!/usr/bin/env  bash
set -o errexit
set -o pipefail
set -o nounset

# Remove the old file if there is one
rm owid.db || true
rm owid.db.gz || true
# Run mysqldump with a subset of tables and some flags to bring it into the required format, the
# pipe this into mysql2sqlite and pipe this into sqlite3 to created owid.db
mysqldump --skip-extended-insert --no-tablespaces --column-statistics=0 --compact --port \
    $DB_PORT --password=$DB_PASSWD --user $DB_USER --host $DB_HOST $DB_NAME \
    users \
    variables \
    tags \
    sources \
    posts \
    post_tags \
    namespaces \
    datasets \
    dataset_tags \
    charts \
    chart_tags \
    chart_slug_redirects \
    chart_dimensions \
    details \
    posts_gdocs \
    pageviews \
    images \
    posts_gdocs_x_images \
    posts_gdocs_links \
    posts_gdocs_x_tags \
  | ./mysql2sqlite - \
  | sqlite3 owid.db
# Run the postprocess-db python script. This is the place to censor some rows or add views etc
python process-db/postprocess-db.py owid.db
python process-db/extract-links.py owid.db
# Gzip the file
gzip -9 -c owid.db > owid.db.gz
# And upload to s3
s3cmd put -P owid.db.gz s3://owid-public