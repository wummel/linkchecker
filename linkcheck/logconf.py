# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
"""
Logging configuration
"""
import logging.config
import sys
from . import ansicolor

# application log areas
LOG_ROOT = "linkcheck"
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_CACHE = "linkcheck.cache"
LOG_GUI = "linkcheck.gui"
LOG_THREAD = "linkcheck.thread"
LOG_PLUGIN = "linkcheck.plugin"
lognames = {
    "cmdline": LOG_CMDLINE,
    "checking": LOG_CHECK,
    "cache": LOG_CACHE,
    "gui": LOG_GUI,
    "thread": LOG_THREAD,
    "plugin": LOG_PLUGIN,
    "all": LOG_ROOT,
}

lognamelist = ", ".join(repr(name) for name in lognames)

# logging configuration
configdict = {
    'version': 1,
    'loggers': {
    },
    'root': {
      'level': 'DEBUG',
    },
}

def init_log_config(handler=None):
    """
    Set up the application logging (not to be confused with check
    loggers). When debug is not None it is expected to be a list of
    logger names for which debugging will be enabled.

    """
    for applog in lognames.values():
        # propagate except for root app logger 'linkcheck'
        propagate = (applog != LOG_ROOT)
        configdict['loggers'][applog] = dict(level='INFO', propagate=propagate)

    logging.config.dictConfig(configdict)
    if handler is None:
        handler = ansicolor.ColoredStreamHandler(strm=sys.stderr)
    add_loghandler(handler)


def add_loghandler (handler):
    """Add log handler to root logger LOG_ROOT and set formatting."""
    logging.getLogger(LOG_ROOT).addHandler(handler)
    format = "%(levelname)s %(asctime)s %(threadName)s %(message)s"
    handler.setFormatter(logging.Formatter(format))


def remove_loghandler (handler):
    """Remove log handler from root logger LOG_ROOT."""
    logging.getLogger(LOG_ROOT).removeHandler(handler)


def reset_loglevel():
    """Reset log level to display only warnings and errors."""
    set_loglevel(['all'], logging.WARN)


def set_debug(loggers):
    """Set debugging log level."""
    set_loglevel(loggers, logging.DEBUG)


def set_loglevel(loggers, level):
    """Set logging levels for given loggers."""
    if not loggers:
        return
    if 'all' in loggers:
        loggers = lognames.keys()
    for key in loggers:
        logging.getLogger(lognames[key]).setLevel(level)
