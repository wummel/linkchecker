#!/bin/sh
# this script is intended to be run daily from cron
# adjust as you wish
# GNU GPL Copyright (C) 2004  Bastian Kleineidam

# replace this with your url(s) you want to check separated by whitespace
# urls can also be local files, eg /var/www/index.html
URL="http://www.imadoofus.org/"

PATH="/bin:/usr/bin"
LOGFILE="$HOME/.linkchecker_blacklist"

./linkchecker -Fblacklist/$LOGFILE $URL
# this awk script complains if urls fail for at least two days
[ -r $LOGFILE ] && awk '/^[[:digit:]]+/ {if ($1 > 1) printf "URL %s failed for %d days.", $2, $1; }' $LOGFILE
