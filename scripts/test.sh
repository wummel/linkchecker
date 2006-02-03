#!/bin/sh -e
P=`dirname $0`
RESOURCES=`$P/resources.sh`
if [ $# -eq 0 ]; then
    coverage="--coverage"
fi
$P/run.sh test.py $RESOURCES $coverage -pvcw "$@"
