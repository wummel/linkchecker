# -*- coding: iso-8859-1 -*-
"""test linkname routines"""
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
import linkcheck.linkname

class TestLinkname (unittest.TestCase):
    """test href and image name parsing"""

    def image_name_test (self, txt, expected):
        """helper function calling linkname.image_name()"""
        self.assertEqual(linkcheck.linkname.image_name(txt), expected)

    def href_name_test (self, txt, expected):
        """helper function calling linkname.href_name()"""
        self.assertEqual(linkcheck.linkname.href_name(txt), expected)

    def test_image_name (self):
        """test image name parsing"""
        self.image_name_test("<img src='' alt=''></a>", '')
        self.image_name_test("<img src alt=abc></a>", 'abc')

    def test_href_name (self):
        """test href name parsing"""
        self.href_name_test("<b>guru guru</a>", 'guru guru')
        self.href_name_test("a\njo</a>", "a\njo")
        self.href_name_test("test<</a>", "test<")
        self.href_name_test("test</</a>", "test</")
        self.href_name_test("test</a</a>", "test</a")
        self.href_name_test("test", "")
        self.href_name_test("\n", "")
        self.href_name_test("", "")
        self.href_name_test('"</a>"foo', '"')
        self.href_name_test("<img src='' alt=''></a>", '')
        self.href_name_test("<img src alt=abc></a>", 'abc')


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLinkname))
    return suite

if __name__ == '__main__':
    unittest.main()
