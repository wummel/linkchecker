#!/bin/sh
NETDEV=eth1
if ifconfig $NETDEV | grep RUNNING > /dev/null; then
    echo "--resource=network"
fi

if msgfmt -V > /dev/null 2>&1; then
    echo "--resource=msgfmt"
fi

os=`python -c "import os; print os.name"`
if [ "x$os" = "xposix" ]; then
    echo "--resource=posix"
fi
