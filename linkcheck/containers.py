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


class SetList (list):
    """a list that eliminates all duplicates"""

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
        """set new value, and eliminate a possible duplicate value"""
        # search index idx with self[i] == value
        idx = -1
        for i in range(len(self)):
            if self[i] == value and i != key:
                idx = i
                # break here, there can be only one duplicate
                break
        # insert new value
        super(SetList, self).__setitem__(key, value)
        if idx != -1:
            # remove duplicate
            del self[idx]


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


class LRU (object):
    """
    Implementation of a length-limited O(1) LRU queue.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson. (Licensed under the GPL)
    """

    class Node (object):
        """internal node with pointers to sisters"""

        def __init__ (self, prev, me):
            """initialize pointers and data"""
            self.prev = prev
            self.me = me
            self.next = None

    def __len__ (self):
        """number of stored objects in the queue"""
        return len(self.d)

    def __init__ (self, count, pairs=None):
        """make new queue with given maximum count, and key/value pairs"""
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        if pairs is not None:
            for key, value in pairs:
                self[key] = value

    def __contains__ (self, obj):
        """look if obj is in the queue"""
        return obj in self.d

    def has_key (self, obj):
        """look if obj is in the queue"""
        return self.d.has_key(obj)

    def __getitem__ (self, obj):
        """get stored object data, and mark it as LRU"""
        a = self.d[obj].me
        self[a[0]] = a[1]
        return a[1]

    def __setitem__ (self, obj, val):
        """set given object data, and mark it as LRU"""
        if obj in self.d:
            del self[obj]
        nobj = self.Node(self.last, (obj, val))
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
        """remove object from queue"""
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
        """iterate over stored object values"""
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2

    def iteritems (self):
        """iterate over stored object items"""
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2

    def iterkeys (self):
        """iterate over stored object keys"""
        return iter(self.d)

    def itervalues (self):
        """iterate over stored object values"""
        for i, j in self.iteritems():
            yield j

    def keys (self):
        """iterate over stored object keys"""
        return self.d.keys()

    def setdefault (self, key, failobj=None):
        """get given object data, and mark it as LRU. If it is not already
           stored, store the given failobj."""
        if not self.has_key(key):
            self[key] = failobj
        return self[key]
