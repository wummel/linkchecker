# -*- coding: iso-8859-1 -*-
# Copyright (C) 2003-2007 Bastian Kleineidam
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

import logging
import os
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
    s.write('Traceback:')
    s.write(os.linesep)
    for frame, fname, lineno, method, lines, dummy in reversed(stack):
        s.write('  File %r, line %d, in %s' % (fname, lineno, method))
        s.write(os.linesep)
        s.write('    %s' % lines[0].lstrip())
        if PRINT_LOCALVARS:
            for key, value in frame.f_locals.iteritems():
                s.write("      %s = " % key)
                # be careful not to cause a new error in the error output
                try:
                    s.write(repr(value))
                    s.write(os.linesep)
                except StandardError:
                    s.write("error in repr() call%s" % os.linesep)
    return s.getvalue()


def _log (fun, msg, args, tb=False):
    """
    Log a message with given function and an optional traceback.

    @return: None
    """
    fun(msg, *args)
    if tb:
        # note: get rid of last parts of the stack
        fun(_stack_format(inspect.stack()[2:]))


def debug (logname, msg, *args, **kwargs):
    """
    Log a debug message.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.DEBUG):
        _log(log.debug, msg, args, tb=kwargs.get("tb"))


def info (logname, msg, *args, **kwargs):
    """
    Log an informational message.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.INFO):
        _log(log.info, msg, args, tb=kwargs.get("tb"))


def warn (logname, msg, *args, **kwargs):
    """
    Log a warning.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.WARN):
        _log(log.warn, msg, args, tb=kwargs.get("tb"))


def error (logname, msg, *args, **kwargs):
    """
    Log an error.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.ERROR):
        _log(log.error, msg, args, tb=kwargs.get("tb"))


def critical (logname, msg, *args, **kwargs):
    """
    Log a critical error.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.CRITICAL):
        _log(log.critical, msg, args, tb=kwargs.get("tb"))


def exception (logname, msg, *args, **kwargs):
    """
    Log an exception.

    return: None
    """
    log = logging.getLogger(logname)
    if log.isEnabledFor(logging.ERROR):
        _log(log.exception, msg, args, tb=kwargs.get("tb"))


def is_debug (logname):
    """
    See if logger is on debug level.
    """
    return logging.getLogger(logname).isEnabledFor(logging.DEBUG)


def shutdown ():
    """
    Flush and close all log handlers.
    """
    logging.shutdown()
