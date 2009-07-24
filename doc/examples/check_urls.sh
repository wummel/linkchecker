#!/bin/sh
# Copyright (C) 2004-2009 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Script suitable for cron job URL checking
# Usage:
# check_urls.sh [--cron] [linkchecker options] [urls...]
# 
# And with crontab -e you add for example the following entry:
#
#    # check my site each night
#    10 4 * * * $HOME/bin/check_urls.sh --cron http://mysite.com/
#
# To only get a mail when errors are encountered, you have to disable
# the intro and outro output in a config file $HOME/.linkchecker/cron:
#
#    [text]
#    parts=realurl,result,extern,base,name,parenturl,info,warning,url
#



if which linkchecker > /dev/null; then
    LC=linkchecker
else
    echo "linkchecker binary not found"
    exit 1
fi
LCOPTS="-f$HOME/.linkchecker/cron"
if [ "$1" = "--cron" ]; then
    shift
    LCOPTS="$LCOPTS --no-status"
    D=/dev/null
else
    D=/dev/stdout
fi
echo "Begin checking..." > $D
$LC $LCOPTS "$@"
