# -*- coding: iso-8859-1 -*-
"""main function module for link checking"""
# Copyright (C) 2000-2005  Bastian Kleineidam
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

# imports and checks
import sys
if not hasattr(sys, 'version_info') or \
   sys.version_info < (2, 3, 0, 'final', 0):
    raise SystemExit, "This program requires Python 2.3 or later."
import os
import re

import linkcheck.i18n
import _linkchecker_configdata as configdata

# application log areas
LOG = "linkcheck"
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_CACHE = "linkcheck.cache"
LOG_GUI = "linkcheck.gui"
lognames = {
    "cmdline": LOG_CMDLINE,
    "checking": LOG_CHECK,
    "cache": LOG_CACHE,
    "gui": LOG_GUI,
    "all": LOG,
    }
lognamelist = ", ".join(["%r"%name for name in lognames.keys()])


class LinkCheckerError (Exception):
    """
    Exception to be raised on linkchecker-specific check errors.
    """
    pass


def get_link_pat (arg, strict=False):
    """
    Get a link pattern matcher for intern/extern links.
    Returns a compiled pattern and a negate and strict option.

    @param arg: pattern from config
    @type arg: c{string}
    @param strict: if pattern is to be handled strict
    @type strict: c{bool}
    @return: dictionary with keys 'pattern', 'negate' and 'strict'
    @rtype: c{dict}
    """
    linkcheck.log.debug(LOG_CHECK, "Link pattern %r", arg)
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


# note: don't confuse URL loggers with application logs above
import linkcheck.logger.text
import linkcheck.logger.html
import linkcheck.logger.gml
import linkcheck.logger.sql
import linkcheck.logger.csvlog
import linkcheck.logger.blacklist
import linkcheck.logger.xmllog
import linkcheck.logger.none


# default link logger classes
Loggers = {
    "text": linkcheck.logger.text.TextLogger,
    "html": linkcheck.logger.html.HtmlLogger,
    "gml": linkcheck.logger.gml.GMLLogger,
    "sql": linkcheck.logger.sql.SQLLogger,
    "csv": linkcheck.logger.csvlog.CSVLogger,
    "blacklist": linkcheck.logger.blacklist.BlacklistLogger,
    "xml": linkcheck.logger.xmllog.XMLLogger,
    "none": linkcheck.logger.none.NoneLogger,
}
# for easy printing: a comma separated logger list
LoggerKeys = ", ".join(["%r"%name for name in Loggers.keys()])


def init_i18n ():
    """
    Initialize i18n with the configured locale dir. The environment
    variable LOCPATH can also specify a locale dir.

    @return: C{None}
    """
    locdir = os.environ.get('LOCPATH')
    if locdir is None:
        locdir = os.path.join(configdata.install_data, 'share', 'locale')
    linkcheck.i18n.init(configdata.name, locdir)

