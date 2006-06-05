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

    def setdefault (self, key, def_val=None):
        assert isinstance(key, basestring)
        return dict.setdefault(self, key.lower(), def_val)

    def update (self, other):
        for k, v in other.items():
            dict.__setitem__(self, k.lower(), v)

    def fromkeys (self, iterable, value=None):
        d = CaselessDict()
        for k in iterable:
            dict.__setitem__(d, k.lower(), value)
        return d

    def pop (self, key, def_val=None):
        assert isinstance(key, basestring)
        return dict.pop(self, key.lower(), def_val)


class CaselessSortedDict (CaselessDict):
    """Caseless dictionary with sorted keys."""

    def keys (self):
        return sorted(super(CaselessSortedDict, self).keys())

    def items (self):
        return [(x, self[x]) for x in self.keys()]


class Node (object):
    """
    Internal node with pointers to sisters.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson. (Licensed under the GPL)
    """

    def __init__ (self, prev, me):
        """
        Initialize pointers and data.
        """
        self.prev = prev
        self.me = me
        self.next = None


class LRU (object):
    """
    Implementation of a length-limited O(1) LRU queue.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson. (Licensed under the GPL)
    """

    def __len__ (self):
        """
        Number of stored objects in the queue.
        """
        return len(self.d)

    def __init__ (self, count, pairs=None):
        """
        Make new queue with given maximum count, and key/value pairs.
        """
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        if pairs is not None:
            for key, value in pairs.items():
                self[key] = value

    def __contains__ (self, obj):
        """Look if obj is in the queue."""
        return obj in self.d

    def has_key (self, obj):
        """Look if obj is in the queue."""
        return self.d.has_key(obj)

    def __getitem__ (self, obj):
        """Get stored object data, and mark it as LRU."""
        a = self.d[obj].me
        self[a[0]] = a[1]
        return a[1]

    def __setitem__ (self, obj, val):
        """Set given object data, and mark it as LRU."""
        if obj in self.d:
            del self[obj]
        nobj = Node(self.last, (obj, val))
        if self.first is None:
            self.first = nobj
        if self.last:
            self.last.next = nobj
        self.last = nobj
        self.d[obj] = nobj
        if len(self.d) > self.count:
            if self.first == self.last:
                self.first = None
                self.last = None
                return
            a = self.first
            a.next.prev = None
            self.first = a.next
            a.next = None
            del self.d[a.me[0]]
            del a

    def __delitem__ (self, obj):
        """Remove object from queue."""
        nobj = self.d[obj]
        if nobj.prev:
            nobj.prev.next = nobj.next
        else:
            self.first = nobj.next
        if nobj.next:
            nobj.next.prev = nobj.prev
        else:
            self.last = nobj.prev
        del self.d[obj]

    def __iter__ (self):
        """Iterate over stored object values."""
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2

    def iteritems (self):
        """Iterate over stored object items."""
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2

    def iterkeys (self):
        """Iterate over stored object keys."""
        return iter(self.d)

    def itervalues (self):
        """Iterate over stored object values."""
        for dummy, j in self.iteritems():
            yield j

    def keys (self):
        """Iterate over stored object keys."""
        return self.d.keys()

    def setdefault (self, key, failobj=None):
        """
        Get given object data, and mark it as LRU. If it is not already
        stored, store the given failobj.
        """
        if not self.has_key(key):
            self[key] = failobj
        return self[key]
