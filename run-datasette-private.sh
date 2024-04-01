#!/bin/bash -e

poetry run datasette ../private-db/owid.db -h 0.0.0.0 -p 8001 --static assets:static-files/ --cors -m metadata.yml --setting sql_time_limit_ms 4000 --setting default_cache_ttl 3600 --setting max_returned_rows 6000 --setting facet_time_limit_ms 1000
