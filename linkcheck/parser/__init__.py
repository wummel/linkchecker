# -*- coding: iso-8859-1 -*-
"""Fast HTML parser module written in C"""
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

__version__ = "$Revision$"[11:-2]
__date__    = "$Date$"[7:-2]

import re, htmlentitydefs

def _resolve_entity (mo):
    """resolve one &#XXX; entity"""
    # convert to number
    ent = mo.group()
    num = mo.group("num")
    if ent.startswith('&#x'):
        radix = 16
    else:
        radix = 10
    num = int(num, radix)
    # check 7-bit ASCII char range
    if 0<=num<=127:
        return chr(num)
    # not in range
    return ent


def resolve_entities (s):
    """resolve entities in 7-bit ASCII range to eliminate obfuscation"""
    return re.sub(r'(?i)&#x?(?P<num>\d+);', _resolve_entity, s)

entities = htmlentitydefs.entitydefs.items()

UnHtmlTable = map(lambda x: ("&"+x[0]+";", x[1]), entities)
# order matters!
UnHtmlTable.sort()
UnHtmlTable.reverse()

def applyTable (table, s):
    "apply a table of replacement pairs to str"
    for mapping in table:
        s = s.replace(mapping[0], mapping[1])
    return s


def resolve_html_entities (s):
    return applyTable(UnHtmlTable, s)


def strip_quotes (s):
    """remove possible double or single quotes"""
    if (s.startswith("'") and s.endswith("'")) or \
       (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s


def _test ():
    print resolve_entities("&#%d;"%ord('a'))

if __name__=='__main__':
    _test()
