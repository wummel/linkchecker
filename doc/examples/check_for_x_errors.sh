#!/bin/sh
# This script is in the public domain.
# Author of this script is Daniel Webb
# Modified by Bastian Kleineidam:
# - added hash-bang first line
# - documentation
# - removed second function, run them commands as-is
# - use $TMPDIR if it exists
#
# Check web site links once per day, report only when the check had more
# than X errors.
#   Return 0
# arguments:
#   $1 - web site URL
#   $2 - notification email
#   $3 - threshold number of errors
#
die() { echo "$0: $*"; exit 1; }

logfile=${TMPDIR-/tmp}/linkchecker.log
[ -z "$1" -o -z "$2" -o -z "$3" ] && die "check_web_links requires three arguments"
do_check=false
if [ ! -f $logfile ]; then
    do_check=true
else
    # Has it been at least a day since last check?
    find $logfile -mtime +1 | grep link && do_check=true
fi
if [ $do_check = true ]; then
    linkchecker $1 >$logfile 2>/dev/null
    errors=$(grep Error: $logfile | wc -l)
    if [ $errors -gt $3 ]; then
        cat $logfile | mail -s "linkchecker: more than $3 errors" $2
    fi
fi
return 0
