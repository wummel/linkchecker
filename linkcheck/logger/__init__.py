# -*- coding: iso-8859-1 -*-
"""Output logging support for different formats"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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
import linkcheck
import linkcheck.i18n


def strtime (t):
    """return ISO 8601 formatted time"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)) + \
           strtimezone()


def strduration (duration):
    """return string formatted time duration"""
    name = linkcheck.i18n._("seconds")
    if duration > 60:
        duration = duration / 60
        name = linkcheck.i18n._("minutes")
    if duration > 60:
        duration = duration / 60
        name = linkcheck.i18n._("hours")
    return " %.3f %s"%(duration, name)


def strtimezone ():
    """return timezone info, %z on some platforms, but not supported on all"""
    if time.daylight:
        zone = time.altzone
    else:
        zone = time.timezone
    return "%+04d" % int(-zone/3600)


import linkcheck.logger.StandardLogger
import linkcheck.logger.HtmlLogger
import linkcheck.logger.ColoredLogger
import linkcheck.logger.GMLLogger
import linkcheck.logger.SQLLogger
import linkcheck.logger.CSVLogger
import linkcheck.logger.BlacklistLogger
import linkcheck.logger.XMLLogger
import linkcheck.logger.NoneLogger


# default logger classes
Loggers = {
    "text": linkcheck.logger.StandardLogger.StandardLogger,
    "html": linkcheck.logger.HtmlLogger.HtmlLogger,
    "colored": linkcheck.logger.ColoredLogger.ColoredLogger,
    "gml": linkcheck.logger.GMLLogger.GMLLogger,
    "sql": linkcheck.logger.SQLLogger.SQLLogger,
    "csv": linkcheck.logger.CSVLogger.CSVLogger,
    "blacklist": linkcheck.logger.BlacklistLogger.BlacklistLogger,
    "xml": linkcheck.logger.XMLLogger.XMLLogger,
    "none": linkcheck.logger.NoneLogger.NoneLogger,
}
# for easy printing: a comma separated logger list
LoggerKeys = ", ".join(Loggers.keys())
