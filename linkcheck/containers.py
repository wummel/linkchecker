# -*- coding: iso-8859-1 -*-
"""special container classes"""
# Copyright (C) 2004  Bastian Kleineidam
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


class SetList (list):
    """a list that eliminates all duplicates
    """

    def append (self, x):
        """append only if not already there"""
        if x not in self:
            super(SetList, self).append(x)

    def extend (self, x):
        """extend while eliminating duplicates by appending item for item"""
        for i in x:
            self.append(i)

    def insert (self, i, x):
        """insert only if not already there"""
        if x not in self:
            super(SetList, self).insert(i, x)

    def __setitem__ (self, key, value):
        """set new value, and eliminate old duplicates (if any)"""
        oldvalues = []
        for i in range(len(self)):
            if self[i]==value:
                oldvalues.append(i)
        super(SetList, self).__setitem__(key, value)
        # remove old duplicates (from last to first)
        oldvalues.reverse()
        for i in oldvalues:
            if i!=key:
                del self[key]


class ListDict (dict):
    """a dictionary whose iterators reflect the order in which elements
       were added
    """

    def __init__ (self):
        """initialize sorted key list"""
        # sorted list of keys
        self._keys = []

    def __setitem__ (self, key, value):
        """add key,value to dict, append key to sorted list"""
        if not self.has_key(key):
            self._keys.append(key)
        super(ListDict, self).__setitem__(key, value)

    def __delitem__ (self, key):
        """remove key from dict"""
        self._keys.remove(key)
        super(ListDict, self).__delitem__(key)

    def values (self):
        """return sorted list of values"""
        return [self[k] for k in self._keys]

    def items (self):
        """return sorted list of items"""
        return [(k, self[k]) for k in self._keys]

    def keys (self):
        """return sorted list of keys"""
        return self._keys[:]

    def itervalues (self):
        """return iterator over sorted values"""
        return iter(self.values())

    def iteritems (self):
        """return iterator over sorted items"""
        return iter(self.items())

    def iterkeys (self):
        """return iterator over sorted keys"""
        return iter(self.keys())

    def clear (self):
        """remove all dict entires"""
        self._keys = []
        super(ListDict, self).clear()

