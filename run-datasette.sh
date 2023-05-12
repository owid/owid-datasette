#/bin/bash
set -o errexit
set -o pipefail
set -o nounset

poetry run datasette -h 0.0.0.0 --cors .