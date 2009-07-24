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
# This script is intended to be run daily from cron. It complains when
# URLs fail for at least a number of script runs.
LOGFILE="$HOME/.linkchecker/blacklist"
linkchecker -Fblacklist "$@"
# this awk script complains if urls fail for at least two script runs
[ -r $LOGFILE ] && awk '/^[[:digit:]]+/ {if ($1 > 1) printf "URL %s failed for %d days.", $2, $1; }' $LOGFILE
