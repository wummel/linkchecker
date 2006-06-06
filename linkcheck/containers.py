# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2006 Bastian Kleineidam
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
Special container classes.
"""


class SetList (list):
    """
    A list that eliminates all duplicates.
    """

    def append (self, item):
        """Append only if not already there."""
        if item not in self:
            super(SetList, self).append(item)

    def extend (self, itemlist):
        """Extend while eliminating duplicates by appending item for item."""
        for item in itemlist:
            self.append(item)

    def insert (self, index, item):
        """Insert item at given index only if it is not already there."""
        if item not in self:
            super(SetList, self).insert(index, item)

    def __setitem__ (self, index, item):
        """Set new value, and eliminate a possible duplicate value."""
        # search index i with self[i] == item
        delidx = -1
        for i in xrange(len(self)):
            if self[i] == item and i != index:
                delidx = i
                # stop here, there can be only one duplicate
                break
        # set new value
        super(SetList, self).__setitem__(index, item)
        # remove duplicate
        if delidx != -1:
            del self[delidx]


class ListDict (dict):
    """
    A dictionary whose iterators reflect the order in which elements
    were added.
    """

    def __init__ (self):
        """Initialize sorted key list."""
        super(ListDict, self).__init__()
        # sorted list of keys
        self._keys = []

    def __setitem__ (self, key, value):
        """Add key,value to dict, append key to sorted list."""
        if not self.has_key(key):
            self._keys.append(key)
        super(ListDict, self).__setitem__(key, value)

    def __delitem__ (self, key):
        """Remove key from dict."""
        self._keys.remove(key)
        super(ListDict, self).__delitem__(key)

    def values (self):
        """Return sorted list of values."""
        return [self[k] for k in self._keys]

    def items (self):
        """Return sorted list of items."""
        return [(k, self[k]) for k in self._keys]

    def keys (self):
        """Return sorted list of keys."""
        return self._keys[:]

    def itervalues (self):
        """Return iterator over sorted values."""
        return iter(self.values())

    def iteritems (self):
        """Return iterator over sorted items."""
        return iter(self.items())

    def iterkeys (self):
        """Return iterator over sorted keys."""
        return iter(self.keys())

    def clear (self):
        """Remove all dict entries."""
        self._keys = []
        super(ListDict, self).clear()

    def get_true (self, key, default):
        """
        Return default element if key is not in the dict, or if self[key]
        evaluates to False. Useful for example if value is None, but
        default value should be an empty string.
        """
        if key not in self or not self[key]:
            return default
        return self[key]


class CaselessDict (dict):
    """A dictionary ignoring the case of keys (which must be strings)."""

    def __init__ (self):
        dict.__init__(self)

    def __getitem__ (self, key):
        assert isinstance(key, basestring)
        return dict.__getitem__(self, key.lower())

    def __delitem__ (self, key):
        assert isinstance(key, basestring)
        return dict.__delitem__(self, key.lower())

    def __setitem__ (self, key, value):
        assert isinstance(key, basestring)
        dict.__setitem__(self, key.lower(), value)

    def __contains__ (self, key):
        assert isinstance(key, basestring)
        return dict.__contains__(self, key.lower())

    def has_key (self, key):
        assert isinstance(key, basestring)
        return dict.has_key(self, key.lower())

    def get (self, key, def_val=None):
        assert isinstance(key, basestring)
        return dict.get(self, key.lower(), def_val)

    def setdefault (self, key, *args):
        assert isinstance(key, basestring)
        return dict.setdefault(self, key.lower(), *args)

    def update (self, other):
        for k, v in other.items():
            dict.__setitem__(self, k.lower(), v)

    def fromkeys (cls, iterable, value=None):
        d = cls()
        for k in iterable:
            dict.__setitem__(d, k.lower(), value)
        return d
    fromkeys = classmethod(fromkeys)

    def pop (self, key, *args):
        assert isinstance(key, basestring)
        return dict.pop(self, key.lower(), *args)


class CaselessSortedDict (CaselessDict):
    """Caseless dictionary with sorted keys."""

    def keys (self):
        return sorted(super(CaselessSortedDict, self).keys())

    def items (self):
        return [(x, self[x]) for x in self.keys()]
