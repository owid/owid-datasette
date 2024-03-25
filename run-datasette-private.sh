#!/bin/bash -e

poetry run datasette owid-private.db -h 0.0.0.0 -p 8001 --static assets:static-files/ --cors
