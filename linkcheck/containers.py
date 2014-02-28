# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Special container classes.
"""

from collections import namedtuple

class AttrDict (dict):
    """Dictionary allowing attribute access to its elements if they
    are valid attribute names and not already existing methods."""

    def __getattr__ (self, name):
        """Return attribute name from dict."""
        return self[name]


class ListDict (dict):
    """A dictionary whose iterators reflect the order in which elements
    were added.
    """

    def __init__ (self):
        """Initialize sorted key list."""
        super(ListDict, self).__init__()
        # sorted list of keys
        self._keys = []

    def setdefault (self, key, *args):
        """Remember key order if key not found."""
        if key not in self:
            self._keys.append(key)
        return super(ListDict, self).setdefault(key, *args)

    def __setitem__ (self, key, value):
        """Add key,value to dict, append key to sorted list."""
        if key not in self:
            self._keys.append(key)
        super(ListDict, self).__setitem__(key, value)

    def __delitem__ (self, key):
        """Remove key from dict."""
        self._keys.remove(key)
        super(ListDict, self).__delitem__(key)

    def pop (self, key):
        """Remove key from dict and return value."""
        if key in self._keys:
            self._keys.remove(key)
        super(ListDict, self).pop(key)

    def popitem (self):
        """Remove oldest key from dict and return item."""
        if self._keys:
            k = self._keys[0]
            v = self[k]
            del self[k]
            return (k, v)
        raise KeyError("popitem() on empty dictionary")

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
        for k in self._keys:
            yield self[k]

    def iteritems (self):
        """Return iterator over sorted items."""
        for k in self._keys:
            yield (k, self[k])

    def iterkeys (self):
        """Return iterator over sorted keys."""
        return iter(self._keys)

    def clear (self):
        """Remove all dict entries."""
        self._keys = []
        super(ListDict, self).clear()

    def get_true (self, key, default):
        """Return default element if key is not in the dict, or if self[key]
        evaluates to False. Useful for example if value is None, but
        default value should be an empty string.
        """
        if key not in self or not self[key]:
            return default
        return self[key]


class CaselessDict (dict):
    """A dictionary ignoring the case of keys (which must be strings)."""

    def __getitem__ (self, key):
        """Return lowercase key item."""
        assert isinstance(key, basestring)
        return dict.__getitem__(self, key.lower())

    def __delitem__ (self, key):
        """Remove lowercase key item."""
        assert isinstance(key, basestring)
        return dict.__delitem__(self, key.lower())

    def __setitem__ (self, key, value):
        """Set lowercase key item."""
        assert isinstance(key, basestring)
        dict.__setitem__(self, key.lower(), value)

    def __contains__ (self, key):
        """Check lowercase key item."""
        assert isinstance(key, basestring)
        return dict.__contains__(self, key.lower())

    def get (self, key, def_val=None):
        """Return lowercase key value."""
        assert isinstance(key, basestring)
        return dict.get(self, key.lower(), def_val)

    def setdefault (self, key, *args):
        """Set lowercase key value and return."""
        assert isinstance(key, basestring)
        return dict.setdefault(self, key.lower(), *args)

    def update (self, other):
        """Update this dict with lowercase key from other dict"""
        for k, v in other.items():
            dict.__setitem__(self, k.lower(), v)

    def fromkeys (cls, iterable, value=None):
        """Construct new caseless dict from given data."""
        d = cls()
        for k in iterable:
            dict.__setitem__(d, k.lower(), value)
        return d
    fromkeys = classmethod(fromkeys)

    def pop (self, key, *args):
        """Remove lowercase key from dict and return value."""
        assert isinstance(key, basestring)
        return dict.pop(self, key.lower(), *args)


class CaselessSortedDict (CaselessDict):
    """Caseless dictionary with sorted keys."""

    def keys (self):
        """Return sorted key list."""
        return sorted(super(CaselessSortedDict, self).keys())

    def items (self):
        """Return sorted item list."""
        return [(x, self[x]) for x in self.keys()]

    def iteritems (self):
        """Return sorted item iterator."""
        return ((x, self[x]) for x in self.keys())


class LFUCache (dict):
    """Limited cache which purges least frequently used items."""

    def __init__ (self, size=1000):
        """Initialize internal LFU cache."""
        super(LFUCache, self).__init__()
        if size < 1:
            raise ValueError("invalid cache size %d" % size)
        self.size = size

    def __setitem__ (self, key, val):
        """Store given key/value."""
        if key in self:
            # store value, do not increase number of uses
            super(LFUCache, self).__getitem__(key)[1] = val
        else:
            super(LFUCache, self).__setitem__(key, [0, val])
            # check for size limit
            if len(self) > self.size:
                self.shrink()

    def shrink (self):
        """Shrink ca. 5% of entries."""
        trim = int(0.05*len(self))
        if trim:
            items = super(LFUCache, self).items()
            # sorting function for items
            keyfunc = lambda x: x[1][0]
            values = sorted(items, key=keyfunc)
            for item in values[0:trim]:
                del self[item[0]]

    def __getitem__ (self, key):
        """Update key usage and return value."""
        entry = super(LFUCache, self).__getitem__(key)
        entry[0] += 1
        return entry[1]

    def uses (self, key):
        """Get number of uses for given key (without increasing the number of
        uses)"""
        return super(LFUCache, self).__getitem__(key)[0]

    def get (self, key, def_val=None):
        """Update key usage if found and return value, else return default."""
        if key in self:
            return self[key]
        return def_val

    def setdefault (self, key, def_val=None):
        """Update key usage if found and return value, else set and return
        default."""
        if key in self:
            return self[key]
        self[key] = def_val
        return def_val

    def items (self):
        """Return list of items, not updating usage count."""
        return [(key, value[1]) for key, value in super(LFUCache, self).items()]

    def iteritems (self):
        """Return iterator of items, not updating usage count."""
        for key, value in super(LFUCache, self).items():
            yield (key, value[1])

    def values (self):
        """Return list of values, not updating usage count."""
        return [value[1] for value in super(LFUCache, self).values()]

    def itervalues (self):
        """Return iterator of values, not updating usage count."""
        for value in super(LFUCache, self).values():
            yield value[1]

    def popitem (self):
        """Remove and return an item."""
        key, value = super(LFUCache, self).popitem()
        return (key, value[1])

    def pop (self):
        """Remove and return a value."""
        value = super(LFUCache, self).pop()
        return value[1]


def enum (*names):
    """Return an enum datatype instance from given list of keyword names.
    The enum values are zero-based integers.

    >>> Status = enum('open', 'pending', 'closed')
    >>> Status.open
    0
    >>> Status.pending
    1
    >>> Status.closed
    2
    """
    return namedtuple('Enum', ' '.join(names))(*range(len(names)))
