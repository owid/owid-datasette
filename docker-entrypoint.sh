#!/usr/bin/env  bash
set -o errexit
set -o pipefail
set -o nounset

wget -O - https://files.ourworldindata.org/owid.db.gz | gunzip -c > /tmp/owid.db
datasette -h 0.0.0.0 --cors -m metadata.yml --setting sql_time_limit_ms 1800 --setting default_cache_ttl 3600 /tmp/owid.db