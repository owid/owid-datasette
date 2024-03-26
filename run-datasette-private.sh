#!/bin/bash -e

poetry run datasette ../private-db/owid.db -h 0.0.0.0 -p 8001 --static assets:static-files/ --cors
