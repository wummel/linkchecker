#!/bin/sh
# this script is intended to be run daily from cron
# GNU GPL Copyright (C) 2004-2005  Bastian Kleineidam

# Put here your url(s) you want to check, separated by whitespace.
# Urls can also be local files, eg "/var/www/index.html".
URL="http://www.imadoofus.org/"

PATH="/bin:/usr/bin"
LOGFILE="$HOME/.linkchecker/blacklist"

linkchecker -Fblacklist $URL
# this awk script complains if urls fail for at least two script runs
[ -r $LOGFILE ] && awk '/^[[:digit:]]+/ {if ($1 > 1) printf "URL %s failed for %d days.", $2, $1; }' $LOGFILE
