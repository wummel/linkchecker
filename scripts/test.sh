#!/bin/sh -e
P=`dirname $0`
RESOURCES=`$P/resources.sh`
if [ $# -eq 0 ]; then
    coverage="--coverage"
fi
$P/run.sh test.py $RESOURCES $coverage -pvcw "$@"
if [ $# -eq 0 ]; then
    # remove files with 100% coverage
    rm `grep -L '>>>>>>' coverage/*.cover`
    # don't care for these ones
    rm coverage/*tests.*.cover || true
    rm coverage/linkcheck.dns.*.cover || true
    rm coverage/linkcheck.httplib2.cover || true
    rm coverage/linkcheck.gzip2.cover || true
    # don't know why these are not filtered
    rm coverage/_xmlplus.*.cover || true
    rm coverage/encodings.*.cover || true
    rm coverage/email.*.cover || true
    rm coverage/logging.*.cover || true
    rm coverage/psyco.*.cover || true
    rm coverage/xml.*.cover || true
fi
