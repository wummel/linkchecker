# -*- coding: iso-8859-1 -*-
"""test string formatting operations"""
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

import unittest
import os

import linkcheck.strformat


class TestStrFormat (unittest.TestCase):
    """test string formatting routines"""

    def test_unquote (self):
        """test quote stripping"""
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
        """test line wrapping"""
        s = "11%(sep)s22%(sep)s33%(sep)s44%(sep)s55" % {'sep': os.linesep}
        # testing width <= 0
        self.assertEquals(linkcheck.strformat.wrap(s, -1), s)
        self.assertEquals(linkcheck.strformat.wrap(s, 0), s)
        s2 = "11 22%(sep)s33 44%(sep)s55" % {'sep': os.linesep}
        # splitting lines
        self.assertEquals(linkcheck.strformat.wrap(s2, 2), s)
        # combining lines
        self.assertEquals(linkcheck.strformat.wrap(s, 5), s2)

    def test_remove_markup (self):
        """test markup removing"""
        self.assertEquals(linkcheck.strformat.remove_markup("<a>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("<>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("<<>"), "")
        self.assertEquals(linkcheck.strformat.remove_markup("a < b"), "a < b")

    def test_strsize (self):
        """test byte size strings"""
        self.assertRaises(ValueError, linkcheck.strformat.strsize, -1)
        self.assertEquals(linkcheck.strformat.strsize(0), "0 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1), "1 Byte")
        self.assertEquals(linkcheck.strformat.strsize(2), "2 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1023), "1023 Bytes")
        self.assertEquals(linkcheck.strformat.strsize(1024), "1.00 kB")


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStrFormat))
    return suite

if __name__ == '__main__':
    unittest.main()
