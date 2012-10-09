#!/bin/sh
# Run the top 1 million URLs as reported by alexa site monitoring.
# The logfile should be checked for
# - unusual errors and warnings,
# - missing recursion when robots.txt is allowed
# The error file should be checked for
# - internal errors
# - program errors (ie. segmentation fault)
#
# Note that the result can depend on the current location.
# Some sites have geo-location-aware content.
set -u
LANG=C
logfile=alexa_1m.log
errfile=alexa_1m_err.log
rm -f $logfile $errfile
for url in $(shuf $HOME/src/alexatopsites/top-1m.txt); do
  echo "Checking $url" | tee -a $logfile | tee -a $errfile
  ./linkchecker -r1 --no-status -Dall $url >> $logfile 2>>$errfile
done
