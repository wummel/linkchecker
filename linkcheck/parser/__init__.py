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

class SortedDict (dict):
    """a dictionary whose listing functions for keys and values preserve
       the order in which elements were added
    """
    def __init__ (self):
        # sorted list of keys
        self._keys = []


    def __setitem__ (self, key, value):
        if not self.has_key(key):
            self._keys.append(key)
        super(SortedDict, self).__setitem__(key, value)


    def __delitem__ (self, key):
        self._keys.remove(key)
        super(SortedDict, self).__delitem__(key)


    def values (self):
        return [self[k] for k in self._keys]


    def items (self):
        return [(k, self[k]) for k in self._keys]


    def keys (self):
        return self._keys[:]


    def itervalues (self):
        return iter(self.values())


    def iteritems (self):
        return iter(self.items())


    def iterkeys (self):
        return iter(self.keys())


    def clear (self):
        self._keys = []
        super(SortedDict, self).clear()


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

UnHtmlTable = [("&"+x[0]+";", x[1]) for x in entities]
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

