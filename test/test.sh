#!/bin/sh
# network device, change as appropriate
NETDEV=eth1
if ifconfig $NETDEV | grep RUNNING > /dev/null; then
    echo "Network resource available"
    RES_NETWORK="--resource=network"
else
    echo "Network disabled"
    RES_NETWORK=""
fi
test/run.sh test.py $RES_NETWORK --search-in=linkcheck -fupvcw "$@"
