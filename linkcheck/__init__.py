# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
"""
Main function module for link checking.
"""

# imports and checks
import sys
if not hasattr(sys, 'version_info') or \
   sys.version_info < (2, 4, 0, 'final', 0):
    raise SystemExit("This program requires Python 2.4 or later.")
import os
import re

import i18n
import _linkchecker_configdata as configdata

# application log areas
LOG = "linkcheck"
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_DNS = "linkcheck.dns"
LOG_CACHE = "linkcheck.cache"
LOG_GUI = "linkcheck.gui"
LOG_THREAD = "linkcheck.thread"
lognames = {
    "cmdline": LOG_CMDLINE,
    "checking": LOG_CHECK,
    "cache": LOG_CACHE,
    "gui": LOG_GUI,
    "dns": LOG_DNS,
    "thread": LOG_THREAD,
    "all": LOG,
    }
lognamelist = ", ".join(["%r"%name for name in lognames.iterkeys()])

import log


class LinkCheckerError (StandardError):
    """
    Exception to be raised on linkchecker-specific check errors.
    """
    pass


def add_intern_pattern (url_data, config):
    """
    Add intern URL regex to config.
    """
    pat = url_data.get_intern_pattern()
    if pat:
        assert None == log.debug(LOG_CHECK,
           "Add intern pattern %r from command line", pat)
        config['internlinks'].append(get_link_pat(pat))


def get_link_pat (arg, strict=False):
    """
    Get a link pattern matcher for intern/extern links.
    Returns a compiled pattern and a negate and strict option.

    @param arg: pattern from config
    @type arg: string
    @param strict: if pattern is to be handled strict
    @type strict: bool
    @return: dictionary with keys 'pattern', 'negate' and 'strict'
    @rtype: dict
    """
    assert None == log.debug(LOG_CHECK, "Link pattern %r", arg)
    if arg.startswith('!'):
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
import logger.text
import logger.html
import logger.gml
import logger.dot
import logger.sql
import logger.csvlog
import logger.blacklist
import logger.gxml
import logger.customxml
import logger.none


# default link logger classes
Loggers = {
    "text": logger.text.TextLogger,
    "html": logger.html.HtmlLogger,
    "gml": logger.gml.GMLLogger,
    "dot": logger.dot.DOTLogger,
    "sql": logger.sql.SQLLogger,
    "csv": logger.csvlog.CSVLogger,
    "blacklist": logger.blacklist.BlacklistLogger,
    "gxml": logger.gxml.GraphXMLLogger,
    "xml": logger.customxml.CustomXMLLogger,
    "none": logger.none.NoneLogger,
}
# for easy printing: a comma separated logger list
LoggerKeys = ", ".join(["%r" % name for name in Loggers.iterkeys()])


def init_i18n ():
    """
    Initialize i18n with the configured locale dir. The environment
    variable LOCPATH can also specify a locale dir.

    @return: None
    """
    locdir = os.environ.get('LOCPATH')
    if locdir is None:
        locdir = os.path.join(configdata.install_data, 'share', 'locale')
    i18n.init(configdata.name, locdir)
    # install translated log level names
    import logging
    logging.addLevelName(logging.CRITICAL, _('CRITICAL'))
    logging.addLevelName(logging.ERROR, _('ERROR'))
    logging.addLevelName(logging.WARN, _('WARN'))
    logging.addLevelName(logging.WARNING, _('WARNING'))
    logging.addLevelName(logging.INFO, _('INFO'))
    logging.addLevelName(logging.DEBUG, _('DEBUG'))
    logging.addLevelName(logging.NOTSET, _('NOTSET'))

# initialize i18n, puts _() function into global namespace
init_i18n()
