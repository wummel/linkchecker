#!/bin/sh
# deactivate all debug calls
set -e
set -u

d=$(dirname $0)
base=$(readlink -f $d/../linkcheck)
find "$base" -type f -print0 | xargs -0 sed -i 's/  log.debug(/  #log.debug(/g'
