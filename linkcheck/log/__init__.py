"""Output logging support for different formats"""
# Copyright (C) 2000-2002  Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import time

def strtime (t):
    """return ISO 8601 formatted time"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)) + \
           strtimezone()

def strtimezone ():
    """return timezone info, %z on some platforms, but not supported on all"""
    if time.daylight:
        zone = time.altzone
    else:
        zone = time.timezone
    return "%+04d" % int(-zone/3600)

import linkcheck

LogFields = {
    "realurl": "Real URL",
    "result": "Result",
    "base": "Base",
    "name": "Name",
    "parenturl": "Parent URL",
    "extern": "Extern",
    "info": "Info",
    "warning": "Warning",
    "dltime": "D/L Time",
    "size": "Content Size",
    "checktime": "Check Time",
    "url": "URL",
}
# maximum indent for localized log field names
MaxIndent = max(map(lambda x: len(linkcheck._(x)), LogFields.values()))+1
# map with spaces between field name and value
Spaces = {}
for key,value in LogFields.items():
    Spaces[key] = " "*(MaxIndent - len(linkcheck._(value)))

from StandardLogger import StandardLogger
from HtmlLogger import HtmlLogger
from ColoredLogger import ColoredLogger
from GMLLogger import GMLLogger
from SQLLogger import SQLLogger
from CSVLogger import CSVLogger
from BlacklistLogger import BlacklistLogger
from XMLLogger import XMLLogger

# default logger classes
Loggers = {
    "text": StandardLogger,
    "html": HtmlLogger,
    "colored": ColoredLogger,
    "gml": GMLLogger,
    "sql": SQLLogger,
    "csv": CSVLogger,
    "blacklist": BlacklistLogger,
    "xml": XMLLogger,
}
# for easy printing: a comma separated logger list
LoggerKeys = reduce(lambda x, y: x+", "+y, Loggers.keys())
