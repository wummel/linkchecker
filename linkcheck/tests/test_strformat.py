# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2005  Bastian Kleineidam
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
Test string formatting operations.
"""

import unittest
import os

import linkcheck.strformat


class TestStrFormat (unittest.TestCase):
    """
    Test string formatting routines.
    """

    def test_unquote (self):
        """
        Test quote stripping.
        """
        self.assertEquals(linkcheck.strformat.unquote(""), "")
        self.assertEquals(linkcheck.strformat.unquote(None), None)
        self.assertEquals(linkcheck.strformat.unquote("'"), "'")
        self.assertEquals(linkcheck.strformat.unquote("\""), "\"")
        self.assertEquals(linkcheck.strformat.unquote("\"\""), "")
        self.assertEquals(linkcheck.strformat.unquote("''"), "")
        self.assertEquals(linkcheck.strformat.unquote("'a'"), "a")
        self.assertEquals(linkcheck.strformat.unquote("'a\"'"), "a\"")
        self.assertEquals(linkcheck.strformat.unquote("'\"a'"), "\"a")
        self.assertEquals(linkcheck.strformat.unquote('"a\'"'), 'a\'')
        self.assertEquals(linkcheck.strformat.unquote('"\'a"'), '\'a')
        # even mis-matching quotes should be removed...
        self.assertEquals(linkcheck.strformat.unquote("'a\""), "a")
        self.assertEquals(linkcheck.strformat.unquote("\"a'"), "a")

    def test_wrap (self):
        """
        Test line wrapping.
        """
        s = "11%(sep)s22%(sep)s33%(sep)s44%(sep)s55" % {'sep': os.linesep}
        # testing width <= 0
        self.assertEquals(linkcheck.strformat.wrap(s, -1), s)
        self.assertEquals(linkcheck.strformat.wrap(s, 0), s)
        l = len(os.linesep)
        gap = " "*l
        s2 = "11%(gap)s22%(sep)s33%(gap)s44%(sep)s55" % \
             {'sep': os.linesep, 'gap': gap}
        # splitting lines
        self.assertEquals(linkcheck.strformat.wrap(s2, 2), s)
        # combining lines
        self.assertEquals(linkcheck.strformat.wrap(s, 4+l), s2)

    def test_remove_markup (self):
        """
        Test markup removing.
        """
        self.assertEquals(linkcheck.strformat.remove_markup("<a>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("<>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("<<>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("a < b"), "a < b")

    def test_strsize (self):
        """
        Test byte size strings.
        """
        self.assertRaises(ValueError, linkcheck.strformat.strsize, -1)
        self.assertEquals(linkcheck.strformat.strsize(0), "0 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1), "1 Byte")
        self.assertEquals(linkcheck.strformat.strsize(2), "2 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1023), "1023 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1024), "1.00 kB")


def test_suite ():
    """
    Build and return a TestSuite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStrFormat))
    return suite

if __name__ == '__main__':
    unittest.main()
