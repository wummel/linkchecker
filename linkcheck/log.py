# -*- coding: iso-8859-1 -*-
"""
Logging and debug functions.
"""
# Copyright (C) 2003-2005  Bastian Kleineidam
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

# public api
__all__ = ["debug", "info", "warn", "error", "critical", "exception", ]

import logging

# memory leak debugging
#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)
def debug (log, msg, *args):
    """
    Log a debug message.

    return: c{None}
    """
    logging.getLogger(log).debug(msg, *args)


def info (log, msg, *args):
    """
    Log an informational message.

    return: c{None}
    """
    logging.getLogger(log).info(msg, *args)


def warn (log, msg, *args):
    """
    Log a warning.

    return: c{None}
    """
    logging.getLogger(log).warn(msg, *args)


def error (log, msg, *args):
    """
    Log an error.

    return: c{None}
    """
    logging.getLogger(log).error(msg, *args)


def critical (log, msg, *args):
    """
    Log a critical error.

    return: c{None}
    """
    logging.getLogger(log).critical(msg, *args)


def exception (log, msg, *args):
    """
    Log an exception.

    return: c{None}
    """
    logging.getLogger(log).exception(msg, *args)
