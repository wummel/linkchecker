#!/bin/sh
# this script is intended to be run daily from cron
# adjust as you wish
# GNU GPL Copyright (C) 2004  Bastian Kleineidam

PATH="/bin:/usr/bin"
LOGFILE="$HOME/.linkchecker_blacklist"
URL="http://www.heise.de"

./linkchecker -Fblacklist/$LOGFILE $URL

[ -r $LOGFILE ] && awk '/^[[:digit:]]+/ {if ($1 > 1) printf "URL %s failed for %d days.", $2, $1; }' $LOGFILE
