mysql2sqlite -f owid.sqlite -d $DB_NAME -u $DB_USER \
    --mysql-password $DB_PASSWD -t users variables tags sources posts post_tags namespaces datasets dataset_tags charts \
    -c 500 -V -P $DB_PORT
gzip -9 -c owid.sqlite > owid.sqlite.gz