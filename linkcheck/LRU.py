# -*- coding: iso-8859-1 -*-
"""implementation of an LRU queue"""

class LRU (object):
    """
    Implementation of a length-limited O(1) LRU queue.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson. (Licensed under the GPL)
    """
    class Node (object):
        def __init__ (self, prev, me):
            self.prev = prev
            self.me = me
            self.next = None


    def __init__ (self, count, pairs=[]):
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        for key, value in pairs:
            self[key] = value


    def __contains__ (self, obj):
        return obj in self.d


    def has_key (self, obj):
        return self.d.has_key(obj)


    def __getitem__ (self, obj):
        a = self.d[obj].me
        self[a[0]] = a[1]
        return a[1]


    def __setitem__ (self, obj, val):
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
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2


    def iteritems (self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2


    def iterkeys (self):
        return iter(self.d)


    def itervalues (self):
        for i,j in self.iteritems():
            yield j


    def keys (self):
        return self.d.keys()



def _main ():
    a = LRU(4)
    a['1'] = '1'
    a['2'] = '2'
    a['3'] = '3'
    a['4'] = '4'
    a['5'] = '5'
    for i in a.iteritems():
        print i,
    print
    b = a['2']
    a['6'] = '6'
    for i in a.iteritems():
        print i,
    print
    print a.has_key('1')
    print a.has_key('2')


if __name__=='__main__':
    _main()
