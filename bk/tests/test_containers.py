# -*- coding: iso-8859-1 -*-
"""test container routines"""

import unittest
import random
import bk.containers


class TestListDict (unittest.TestCase):

    def setUp (self):
        self.d = bk.containers.ListDict()

    def test_insert (self):
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.assert_(2 in self.d)
        self.assert_(1 in self.d)

    def test_delete (self):
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        del self.d[1]
        self.assert_(2 in self.d)
        self.assert_(1 not in self.d)

    def test_update (self):
        self.assert_(not self.d)
        self.d[2] = 1
        self.d[1] = 2
        self.d[1] = 1
        self.assertEqual(self.d[1], 1)

    def test_sorting (self):
        self.assert_(not self.d)
        toinsert = random.sample(xrange(10000000), 60)
        for x in toinsert:
            self.d[x] = x
        for i, k in enumerate(self.d.keys()):
            self.assertEqual(self.d[k], toinsert[i])


class TestSetList (unittest.TestCase):

    def setUp (self):
        self.l = bk.containers.SetList()

    def test_append (self):
        self.assert_(not self.l)
        self.l.append(1)
        self.l.append(1)
        self.assertEqual(len(self.l), 1)

    def test_append2 (self):
        self.assert_(not self.l)
        self.l.append(1)
        self.l.append(2)
        self.l.append(1)
        self.assertEqual(len(self.l), 2)

    def test_extend (self):
        self.assert_(not self.l)
        self.l.extend([1, 2, 1])
        self.assertEqual(len(self.l), 2)
        self.assertEqual(self.l[0], 1)
        self.assertEqual(self.l[1], 2)

    def test_setitem (self):
        self.assert_(not self.l)
        self.l.extend([1,2,3])
        self.l[1] = 3
        self.assertEqual(len(self.l), 2)
        self.assertEqual(self.l[0], 1)
        self.assertEqual(self.l[1], 3)


def test_suite ():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestListDict))
    suite.addTest(unittest.makeSuite(TestSetList))
    return suite

if __name__ == '__main__':
    unittest.main()

