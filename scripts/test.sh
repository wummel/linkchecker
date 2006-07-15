#!/bin/sh
P=`dirname $0`
RESOURCES=`$P/resources.sh`
if [ $# -eq 0 ]; then
    coverage="--coverage"
fi
$P/run.sh test.py $RESOURCES $coverage -pvcw "$@"
res=$?
if [ $# -eq 0 ]; then
    # remove files with 100% coverage
    rm `grep -L '>>>>>>' coverage/*.cover`
    # don't care for these ones
    rm coverage/*tests.*.cover
    rm coverage/linkcheck.dns.*.cover
    rm coverage/linkcheck.httplib2.cover
    rm coverage/linkcheck.gzip2.cover
    # don't know why these are not filtered
    rm coverage/_xmlplus.*.cover
    rm coverage/encodings.*.cover
    rm coverage/email.*.cover
    rm coverage/logging.*.cover
    rm coverage/xml.*.cover
fi
exit $res
