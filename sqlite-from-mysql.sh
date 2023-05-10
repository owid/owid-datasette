#!/usr/bin/env  bash
set -o errexit
set -o pipefail
set -o nounset

# Remove the old file if there is one
rm owid.db || true
rm owid-public.db || true
rm owid-private.db || true
rm owid.db.gz || true

set -o allexport
source .env set
set +o allexport

# Run mysqldump with a subset of tables and some flags to bring it into the required format, the
# pipe this into mysql2sqlite and pipe this into sqlite3 to create owid.db.
# we need the additional `sed` command to replace string literals like `_utf8mb4'$.slug'`, which
# mysql generates for generated columns, with just `$.slug`.
# we also need to replace `JSON_UNQUOTE(JSON_EXTRACT())` with just `JSON_EXTRACT()`, because
# always does JSON_UNQUOTE(), but doesn't know the function name.
mysqldump --skip-extended-insert --no-tablespaces --column-statistics=0 --compact --port \
    $DB_PORT --password=$DB_PASSWD --user $DB_USER --host $DB_HOST $DB_NAME \
    users \
    variables \
    entities \
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
    posts_gdocs \
    pageviews \
    images \
    posts_gdocs_x_images \
    posts_gdocs_links \
    posts_gdocs_x_tags \
  | ./mysql2sqlite - \
  | sed 's/_utf8mb4//g' \
  | sed 's/JSON_UNQUOTE(JSON_EXTRACT(/(JSON_EXTRACT(/gi' \
  | sqlite3 owid-public.db
# Run the postprocess-db python script. This is the place to censor some rows or add views etc
cp owid-public.db owid-private.db
python process-db/postprocess-db.py owid-public.db
python process-db/extract-links.py owid-public.db
python process-db/postprocess-db.py --keep-confidential-data owid-private.db
python process-db/extract-links.py owid-private.db
# Gzip the file
gzip -9 -c owid-public.db > owid.db.gz
# And upload to s3
s3cmd put -P owid.db.gz s3://owid-public