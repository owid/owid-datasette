mysql2sqlite -f owid.db -d $DB_NAME -u $DB_USER \
    --mysql-password $DB_PASSWD -t users variables tags sources posts post_tags namespaces datasets dataset_tags charts chart_tags \
    -c 500 -V -P $DB_PORT
python postprocess-db.py
gzip -9 -c owid.db > owid.db.gz