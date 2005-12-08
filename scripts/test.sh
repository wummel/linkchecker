#!/bin/sh
# network device, change as appropriate
P=`dirname $0`
RESOURCES=`$P/resources.sh`
$P/run.sh test.py $RESOURCES --coverage -pvcw "$@"
