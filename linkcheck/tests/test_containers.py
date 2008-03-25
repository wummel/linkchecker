# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2008 Bastian Kleineidam
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
Test container routines.
"""

import unittest
import random
import linkcheck.containers


class TestListDict (unittest.TestCase):
    """
    Test list dictionary routines.
    """

    def setUp (self):
        """
        Set up self.d as empty listdict.
        """
        self.d = linkcheck.containers.ListDict()

    def test_insert (self):
        """
        Test insertion order.
        """
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.assert_(2 in self.d)
        self.assert_(1 in self.d)

    def test_delete (self):
        """
        Test deletion order.
        """
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        del self.d[1]
        self.assert_(2 in self.d)
        self.assert_(1 not in self.d)

    def test_update (self):
        """
        Test update order.
        """
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.d[1] = 1
        self.assertEqual(self.d[1], 1)

    def test_sorting (self):
        """
        Test sorting.
        """
        self.assert_(not self.d)
        toinsert = random.sample(xrange(10000000), 60)
        for x in toinsert:
            self.d[x] = x
        for i, k in enumerate(self.d.keys()):
            self.assertEqual(self.d[k], toinsert[i])
        for i, k in enumerate(self.d.iterkeys()):
            self.assertEqual(self.d[k], toinsert[i])
        for x in self.d.values():
            self.assert_(x in toinsert)
        for x in self.d.itervalues():
            self.assert_(x in toinsert)
        for x, y in self.d.items():
            self.assert_(x in toinsert)
            self.assert_(y in toinsert)
        for x, y in self.d.iteritems():
            self.assert_(x in toinsert)
            self.assert_(y in toinsert)

    def test_clear (self):
        """
        Test clearing.
        """
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 3
        self.d.clear()
        self.assert_(not self.d)

    def test_get_true (self):
        """
        Test getting a non-False object.
        """
        self.assert_(not self.d)
        self.d["a"] = 0
        self.d["b"] = 1
        self.assertEqual(self.d.get_true("a", 2), 2)
        self.assertEqual(self.d.get_true("b", 2), 1)


class TestSetList (unittest.TestCase):
    """
    Test set list routines.
    """

    def setUp (self):
        """
        Set up self.l as empty setlist.
        """
        self.l = linkcheck.containers.SetList()

    def test_append (self):
        """
        Test append and equal elements.
        """
        self.assert_(not self.l)
        self.l.append(1)
        self.l.append(1)
        self.assertEqual(len(self.l), 1)

    def test_append2 (self):
        """
        Test append and equal elements 2.
        """
        self.assert_(not self.l)
        self.l.append(1)
        self.l.append(2)
        self.l.append(1)
        self.assertEqual(len(self.l), 2)

    def test_extend (self):
        """
        Test extend and equal elements.
        """
        self.assert_(not self.l)
        self.l.extend([1, 2, 1])
        self.assertEqual(len(self.l), 2)
        self.assertEqual(self.l[0], 1)
        self.assertEqual(self.l[1], 2)

    def test_insert (self):
        """
        Test insert and equal elements.
        """
        self.assert_(not self.l)
        self.l.append(2)
        self.l.insert(0, 1)
        self.assertEqual(len(self.l), 2)
        self.assertEqual(self.l[0], 1)
        self.assertEqual(self.l[1], 2)

    def test_setitem (self):
        """
        Test setting of equal elements.
        """
        self.assert_(not self.l)
        self.l.extend([1, 2, 3])
        self.l[1] = 3
        self.assertEqual(len(self.l), 2)
        self.assertEqual(self.l[0], 1)
        self.assertEqual(self.l[1], 3)


class TestCaselessDict (unittest.TestCase):
    """
    Test caseless dictionary routines.
    """

    def setUp (self):
        """
        Set up self.d as empty caseless dict.
        """
        self.d = linkcheck.containers.CaselessDict()

    def test_insert (self):
        self.assert_(not self.d)
        self.d["a"] = 1
        self.assert_("a" in self.d)
        self.assert_("A" in self.d)
        self.d["aBcD"] = 2
        self.assert_("abcd" in self.d)
        self.assert_("Abcd" in self.d)
        self.assert_("ABCD" in self.d)

    def test_delete (self):
        self.assert_(not self.d)
        self.d["a"] = 1
        del self.d["A"]
        self.assert_("a" not in self.d)
        self.assert_("A" not in self.d)

    def test_update (self):
        self.assert_(not self.d)
        self.d["a"] = 1
        self.d["A"] = 2
        self.assertEqual(self.d["a"], 2)

    def test_clear (self):
        self.assert_(not self.d)
        self.d["a"] = 5
        self.d["b"] = 6
        self.d.clear()
        self.assert_(not self.d)

    def test_containment (self):
        self.assert_(not self.d)
        self.assert_("A" not in self.d)
        self.assert_("a" not in self.d)
        self.d["a"] = 5
        self.assert_("A" in self.d)
        self.assert_("a" in self.d)

    def test_setdefault (self):
        self.assert_(not self.d)
        self.d["a"] = 5
        self.assertEquals(self.d.setdefault("A", 6), 5)
        self.assertEquals(self.d.setdefault("b", 7), 7)

    def test_get (self):
        self.assert_(not self.d)
        self.d["a"] = 42
        self.assertEquals(self.d.get("A"), 42)
        self.assert_(self.d.get("B") is None)

    def test_update2 (self):
        self.assert_(not self.d)
        self.d["a"] = 42
        self.d.update({"A": 43})
        self.assertEquals(self.d["a"], 43)

    def test_fromkeys (self):
        self.assert_(not self.d)
        keys = ["a", "A", "b", "C"]
        d1 = self.d.fromkeys(keys, 42)
        for key in keys:
            self.assertEquals(d1[key], 42)

    def test_pop (self):
        self.assert_(not self.d)
        self.d["a"] = 42
        self.assertEquals(self.d.pop("A"), 42)
        self.assert_(not self.d)
        self.assertRaises(KeyError, self.d.pop, "A")

    def test_popitem (self):
        self.assert_(not self.d)
        self.d["a"] = 42
        self.assertEquals(self.d.popitem(), ("a", 42))
        self.assert_(not self.d)
        self.assertRaises(KeyError, self.d.popitem)


class TestCaselessSortedDict (unittest.TestCase):
    """
    Test caseless sorted dictionary routines.
    """

    def setUp (self):
        """
        Set up self.d as empty caseless sorted dict.
        """
        self.d = linkcheck.containers.CaselessSortedDict()

    def test_sorted (self):
        self.assert_(not self.d)
        self.d["b"] = 6
        self.d["a"] = 7
        self.d["C"] = 8
        prev = None
        for key in self.d.keys():
            self.assert_(key > prev)
            prev = key
        prev = None
        for key, value in self.d.items():
            self.assert_(key > prev)
            prev = key


def test_suite ():
    """
    Build and return a TestSuite.
    """
    from tests import make_suite
    prefix = __name__.split(".")[-1]
    return make_suite(prefix, globals())


if __name__ == '__main__':
    unittest.main()
