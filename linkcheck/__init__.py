# -*- coding: iso-8859-1 -*-
"""main function module for link checking"""
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

import sys
import re
import time
import linkcheck.i18n


# logger areas
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_DNS = "linkcheck.dns"
LOG_GUI = "linkcheck.gui"


class LinkCheckerError (Exception):
    pass


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


def getLinkPat (arg, strict=False):
    """get a link pattern matcher for intern/extern links"""
    bk.log.debug(LOG_CHECK, "Link pattern %r", arg)
    if arg[0:1] == '!':
        pattern = arg[1:]
        negate = True
    else:
        pattern = arg
        negate = False
    return {
        "pattern": re.compile(pattern),
        "negate": negate,
        "strict": strict,
    }


def printStatus (config, curtime, start_time):
    tocheck = len(config.urls)
    links = config['linknumber']
    active = config.threader.active_threads()
    duration = strduration(curtime - start_time)
    print >>sys.stderr, linkcheck.i18n._("%5d urls queued, %4d links checked, %2d active threads, runtime %s")%\
                               (tocheck, links, active, duration)


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
