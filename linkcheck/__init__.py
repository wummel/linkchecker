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
import bk.i18n
import bk.strtime


# logger areas
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_GUI = "linkcheck.gui"


class LinkCheckerError (Exception):
    pass


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
