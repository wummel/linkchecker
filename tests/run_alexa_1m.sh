#!/bin/sh
# Run the top 1 million URLs as reported by alexa site monitoring.
# The logfile should be searched for internal errors first, then
# all unusual errors and warnings should be inspected.
#
# Note that the result is usually depending on the current location
# from where the tests are run.
set -u
logfile=alexa_1m.log
rm -f $logfile
for url in $(cat $HOME/src/alexatopsites/top-1m.txt); do
  ./linkchecker -r1 $url >> $logfile 2>&1
done

