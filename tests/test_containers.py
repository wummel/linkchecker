# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2011 Bastian Kleineidam
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
Test container routines.
"""

import unittest
import random
import linkcheck.containers


class TestAttrDict (unittest.TestCase):

    def setUp (self):
        self.d = linkcheck.containers.AttrDict()

    def test_access (self):
        self.d["test"] = 1
        self.assertEqual(self.d.test, self.d["test"])
        self.assertEqual(self.d.test, 1)

    def test_method (self):
        self.d["get"] = 1
        self.assertTrue(isinstance(self.d.get, type({}.get)))


class TestListDict (unittest.TestCase):
    """Test list dictionary routines."""

    def setUp (self):
        """Set up self.d as empty listdict."""
        self.d = linkcheck.containers.ListDict()

    def test_insertion_order (self):
        self.assertTrue(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.assertTrue(2 in self.d)
        self.assertTrue(1 in self.d)

    def test_deletion_order (self):
        self.assertTrue(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        del self.d[1]
        self.assertTrue(2 in self.d)
        self.assertTrue(1 not in self.d)

    def test_update_order (self):
        self.assertTrue(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.d[1] = 1
        self.assertEqual(self.d[1], 1)

    def test_sorting (self):
        self.assertTrue(not self.d)
        toinsert = random.sample(xrange(10000000), 60)
        for x in toinsert:
            self.d[x] = x
        for i, k in enumerate(self.d.keys()):
            self.assertEqual(self.d[k], toinsert[i])
        for i, k in enumerate(self.d.iterkeys()):
            self.assertEqual(self.d[k], toinsert[i])
        for x in self.d.values():
            self.assertTrue(x in toinsert)
        for x in self.d.itervalues():
            self.assertTrue(x in toinsert)
        for x, y in self.d.items():
            self.assertTrue(x in toinsert)
            self.assertTrue(y in toinsert)
        for x, y in self.d.iteritems():
            self.assertTrue(x in toinsert)
            self.assertTrue(y in toinsert)

    def test_clear (self):
        self.assertTrue(not self.d)
        self.d[2] = 1
        self.d[1] = 3
        self.d.clear()
        self.assertTrue(not self.d)

    def test_get_true (self):
        self.assertTrue(not self.d)
        self.d["a"] = 0
        self.d["b"] = 1
        self.assertEqual(self.d.get_true("a", 2), 2)
        self.assertEqual(self.d.get_true("b", 2), 1)


class TestCaselessDict (unittest.TestCase):
    """Test caseless dictionary routines."""

    def setUp (self):
        """Set up self.d as empty caseless dict."""
        self.d = linkcheck.containers.CaselessDict()

    def test_insert (self):
        self.assertTrue(not self.d)
        self.d["a"] = 1
        self.assertTrue("a" in self.d)
        self.assertTrue("A" in self.d)
        self.d["aBcD"] = 2
        self.assertTrue("abcd" in self.d)
        self.assertTrue("Abcd" in self.d)
        self.assertTrue("ABCD" in self.d)

    def test_delete (self):
        self.assertTrue(not self.d)
        self.d["a"] = 1
        del self.d["A"]
        self.assertTrue("a" not in self.d)
        self.assertTrue("A" not in self.d)

    def test_update (self):
        self.assertTrue(not self.d)
        self.d["a"] = 1
        self.d["A"] = 2
        self.assertEqual(self.d["a"], 2)

    def test_clear (self):
        self.assertTrue(not self.d)
        self.d["a"] = 5
        self.d["b"] = 6
        self.d.clear()
        self.assertTrue(not self.d)

    def test_containment (self):
        self.assertTrue(not self.d)
        self.assertTrue("A" not in self.d)
        self.assertTrue("a" not in self.d)
        self.d["a"] = 5
        self.assertTrue("A" in self.d)
        self.assertTrue("a" in self.d)

    def test_setdefault (self):
        self.assertTrue(not self.d)
        self.d["a"] = 5
        self.assertEqual(self.d.setdefault("A", 6), 5)
        self.assertEqual(self.d.setdefault("b", 7), 7)

    def test_get (self):
        self.assertTrue(not self.d)
        self.d["a"] = 42
        self.assertEqual(self.d.get("A"), 42)
        self.assertTrue(self.d.get("B") is None)

    def test_update2 (self):
        self.assertTrue(not self.d)
        self.d["a"] = 42
        self.d.update({"A": 43})
        self.assertEqual(self.d["a"], 43)

    def test_fromkeys (self):
        self.assertTrue(not self.d)
        keys = ["a", "A", "b", "C"]
        d1 = self.d.fromkeys(keys, 42)
        for key in keys:
            self.assertEqual(d1[key], 42)

    def test_pop (self):
        self.assertTrue(not self.d)
        self.d["a"] = 42
        self.assertEqual(self.d.pop("A"), 42)
        self.assertTrue(not self.d)
        self.assertRaises(KeyError, self.d.pop, "A")

    def test_popitem (self):
        self.assertTrue(not self.d)
        self.d["a"] = 42
        self.assertEqual(self.d.popitem(), ("a", 42))
        self.assertTrue(not self.d)
        self.assertRaises(KeyError, self.d.popitem)


class TestCaselessSortedDict (unittest.TestCase):
    """Test caseless sorted dictionary routines."""

    def setUp (self):
        """Set up self.d as empty caseless sorted dict."""
        self.d = linkcheck.containers.CaselessSortedDict()

    def test_sorted (self):
        self.assertTrue(not self.d)
        self.d["b"] = 6
        self.d["a"] = 7
        self.d["C"] = 8
        prev = None
        for key in self.d.keys():
            if prev is not None:
                self.assertTrue(key > prev)
            prev = key
        prev = None
        for key, value in self.d.items():
            self.assertEqual(value, self.d[key])
            if prev is not None:
                self.assertTrue(key > prev)
            prev = key


class TestLFUCache (unittest.TestCase):
    """Test LFU cache implementation."""

    def setUp (self):
        """Set up self.d as empty LFU cache with default size of 1000."""
        self.size = 1000
        self.d = linkcheck.containers.LFUCache(self.size)

    def test_num_uses (self):
        self.assertTrue(not self.d)
        self.d["a"] = 1
        self.assertTrue("a" in self.d)
        self.assertEqual(self.d.uses("a"), 0)
        dummy = self.d["a"]
        self.assertEqual(self.d.uses("a"), 1)

    def test_values (self):
        self.assertTrue(not self.d)
        self.d["a"] = 1
        self.d["b"] = 2
        self.assertEqual(set([1, 2]), set(self.d.values()))
        self.assertEqual(set([1, 2]), set(self.d.itervalues()))

    def test_popitem (self):
        self.assertTrue(not self.d)
        self.d["a"] = 42
        self.assertEqual(self.d.popitem(), ("a", 42))
        self.assertTrue(not self.d)
        self.assertRaises(KeyError, self.d.popitem)

    def test_shrink (self):
        self.assertTrue(not self.d)
        for i in range(self.size):
            self.d[i] = i
        self.d[1001] = 1001
        self.assertTrue(950 <= len(self.d) <= self.size)


class TestEnum (unittest.TestCase):

    def test_enum (self):
        e = linkcheck.containers.enum("a", "b", "c")
        self.assertEqual(e.a, 0)
        self.assertEqual(e.b, 1)
        self.assertEqual(e.c, 2)
        self.assertEqual(e, (0, 1, 2))
