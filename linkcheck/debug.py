# -*- coding: iso-8859-1 -*-
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

# debug level constants (Quake-style)
ALWAYS = 0
BRING_IT_ON = 1
HURT_ME_PLENTY = 2
NIGHTMARE = 3

# the global debug level
_debuglevel = 0

def get_debuglevel ():
    return _debuglevel

def set_debuglevel (i):
    if i>=NIGHTMARE:
        import gc
        gc.set_debug(gc.DEBUG_LEAK)
    global _debuglevel
    _debuglevel = i

from AnsiColor import colorize

def _text (*args, **kwargs):
    text = " ".join(map(str, args))
    print >>sys.stderr, colorize(text, color=kwargs.get('color'))

# memory leak debugging
#import gc, os
#gc.set_debug(gc.DEBUG_LEAK)

# debug function, using the debug level
def debug (level, *args):
    #_text("collected %d"%gc.collect())
    #_text("objects %d"%len(gc.get_objects()))
    #_text("garbage %d"%len(gc.garbage))
    #if gc.garbage:
    #    for o in gc.garbage:
    #        _text("O %s"%repr(o))
    #_text("Mem: %s"%usedmemory())
    if level <= _debuglevel:
        _text(*args)

def usedmemory ():
    pid = os.getpid()
    fp = file('/proc/%d/status'%pid)
    try:
        for line in fp.readlines():
            if line.startswith('VmRSS:'):
                return line[6:].strip()
    finally:
        fp.close()
    return val


def info (*args):
    args = list(args)
    args.insert(0, "info:")
    _text(*args, **{'color':'default'})

def warn (*args):
    args = list(args)
    args.insert(0, "warning:")
    _text(*args, **{'color':'bold;yellow'})

def error (*args):
    args = list(args)
    args.insert(0, "error:")
    _text(*args, **{'color':'bold;red'})


def test ():
    debug("a")
    warn("a", "b")
    info(None)
    error()

if __name__=='__main__':
    test()

