#!/bin/sh
# network device, change as appropriate
RESOURCES=`test/resources.sh`
test/run.sh test.py $RESOURCES --coverage -pvcw "$@"
