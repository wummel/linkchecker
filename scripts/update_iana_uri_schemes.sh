#!/bin/sh

set -e
set -u

target=linkcheck/checker/unknownurl.py

python scripts/removeafter.py "$target" "# DO NOT REMOVE"
python scripts/update_iana_uri_schemes.py >> "$target"
