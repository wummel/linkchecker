# -*- coding: iso-8859-1 -*-
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
"""
Logging and debug functions.
"""

# public api
__all__ = ["debug", "info", "warn", "error", "critical", "exception", ]

import logging
import traceback
import inspect
import cStringIO as StringIO

# memory leak debugging
#import gc
#gc.enable()
#gc.set_debug(gc.DEBUG_LEAK)

PRINT_LOCALVARS = False

def _stack_format (stack):
    """
    Format a stack trace to a message.

    @return: formatted stack message
    @rtype: string
    """
    s = StringIO.StringIO()
    traceback.print_stack(stack, file=s)
    if PRINT_LOCALVARS:
        s.write("Locals by frame, innermost last%s" % os.linesep)
        for frame in stack:
            s.write(os.linesep)
            s.write("Frame %s in %s at line %s%s" % (frame.f_code.co_name,
                                                     frame.f_code.co_filename,
                                                     frame.f_lineno,
                                                     os.linesep))
            for key, value in frame.f_locals.items():
                s.write("\t%20s = " % key)
                # be careful not to cause a new error in the error output
                try:
                    s.write(str(value))
                    s.write(os.linesep)
                except:
                    s.write("error in str() call%s" % os.linesep)
    return s.getvalue()


def _log (fun, msg, args, tb=False):
    """
    Log a message with given function and an optional traceback.

    @return: None
    """
    fun(msg, *args)
    if tb:
        # note: get rid of last parts of the stack
        s = _stack_format(inspect.stack()[2:])
        fun(s)


def debug (log, msg, *args, **kwargs):
    """
    Log a debug message.

    return: None
    """
    _log(logging.getLogger(log).debug, msg, args, tb=kwargs.get("tb"))


def info (log, msg, *args, **kwargs):
    """
    Log an informational message.

    return: None
    """
    _log(logging.getLogger(log).info, msg, args, tb=kwargs.get("tb"))


def warn (log, msg, *args, **kwargs):
    """
    Log a warning.

    return: None
    """
    _log(logging.getLogger(log).warn, msg, args, tb=kwargs.get("tb"))


def error (log, msg, *args, **kwargs):
    """
    Log an error.

    return: None
    """
    _log(logging.getLogger(log).error, msg, args, tb=kwargs.get("tb"))


def critical (log, msg, *args, **kwargs):
    """
    Log a critical error.

    return: None
    """
    _log(logging.getLogger(log).critical, msg, args, tb=kwargs.get("tb"))


def exception (log, msg, *args, **kwargs):
    """
    Log an exception.

    return: None
    """
    _log(logging.getLogger(log).exception, msg, args, tb=kwargs.get("tb"))


def is_debug (log):
    """
    See if logger is on debug level.
    """
    return logging.getLogger(log).isEnabledFor(logging.DEBUG)
