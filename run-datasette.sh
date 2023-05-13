#!/bin/bash -e

poetry run datasette -h 0.0.0.0 --static assets:static-files/ --cors .