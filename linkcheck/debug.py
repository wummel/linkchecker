# Copyright (C) 2000-2003  Bastian Kleineidam
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
    global _debuglevel
    _debuglevel = i

from AnsiColor import colorize

def _text (*args, **kwargs):
    text = " ".join(map(str, args))
    print >>sys.stderr, colorize(text, color=kwargs.get('color'))

# debug function, using the debug level
def debug (level, *args):
    if level <= _debuglevel:
        _text(*args)

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

