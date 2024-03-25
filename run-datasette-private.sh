#!/bin/bash -e

poetry run datasette owid-private.sqlite -h 0.0.0.0 -p 8001 --static assets:static-files/ --cors
