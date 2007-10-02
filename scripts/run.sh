#!/bin/sh
# Run python interpreter with current dir as search path, and remove all
# locale and proxy settings.
# Set PYOPTS for options, for example PYOPTS=-O.
PYVER=2.4
env -u ftp_proxy -u http_proxy -u LANGUAGE -u LC_ALL -u LC_CTYPE LANG=C PYTHONPATH=`pwd` python${PYVER} ${PYOPTS:-} "$@"
