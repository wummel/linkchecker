# -*- coding: iso-8859-1 -*-
"""logging and debug functions"""
# Copyright (C) 2003-2004  Bastian Kleineidam
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
__all__ = ["debug", "info", "warn", "error", "critical",
           "exception", "get_log_file", "set_format", "usedmemory"]

import os
import logging


def iswritable (fname):
    """return True if given file is writable"""
    if os.path.isdir(fname) or os.path.islink(fname):
        return False
    try:
        if os.path.exists(fname):
            file(fname, 'a').close()
            return True
        else:
            file(fname, 'w').close()
            os.remove(fname)
            return True
    except IOError:
        pass
    return False


def get_log_file (name, logname, trydirs=[]):
    """get full path name to writeable logfile"""
    dirs = []
    if os.name =='nt':
        dirs.append(os.environ.get("TEMP"))
    else:
        dirs.append(os.path.join('/', 'var', 'log', name))
        dirs.append(os.path.join('/', 'var', 'tmp', name))
        dirs.append(os.path.join('/', 'tmp', name))
    dirs.append(os.getcwd())
    trydirs = trydirs+dirs
    for d in trydirs:
        fullname = os.path.join(d, logname)
        if iswritable(fullname):
            return fullname
    raise IOError("Could not find writable directory for %s in %s" % (logname, str(trydirs)))


def set_format (handler):
    """set standard format for handler"""
    handler.setFormatter(logging.root.handlers[0].formatter)
    return handler


def usedmemory ():
    """return string with used memory"""
    pid = os.getpid()
    fp = file('/proc/%d/status'%pid)
    val = 0
    try:
        for line in fp.readlines():
            if line.startswith('VmRSS:'):
                val = int(line[6:].strip().split()[0])
    finally:
        fp.close()
    return val


import gc
gc.enable()
# memory leak debugging
#gc.set_debug(gc.DEBUG_LEAK)
def debug (log, msg, *args):
    """log a debug message"""
    logging.getLogger(log).debug(msg, *args)
    #logging.getLogger(log).info("Mem: %d kB"%usedmemory())


def info (log, msg, *args):
    """log an informational message"""
    logging.getLogger(log).info(msg, *args)


def warn (log, msg, *args):
    """log a warning"""
    logging.getLogger(log).warn(msg, *args)


def error (log, msg, *args):
    """log an error"""
    logging.getLogger(log).error(msg, *args)


def critical (log, msg, *args):
    """log a critical error"""
    logging.getLogger(log).critical(msg, *args)


def exception (log, msg, *args):
    """log an exception"""
    logging.getLogger(log).exception(msg, *args)
