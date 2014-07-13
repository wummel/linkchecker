#!/bin/bash
# Update the list of unknown and therefore ignored URL schemes.

set -o nounset
set -o errexit
set -o pipefail
#set -o xtrace

target=linkcheck/checker/unknownurl.py

python scripts/removeafter.py "$target" "# DO NOT REMOVE"
python scripts/update_iana_uri_schemes.py >> "$target"
