# -*- coding: iso-8859-1 -*-
"""test html <base> tag parsing"""
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

import linkcheck.ftests

class TestBase (linkcheck.ftests.StandardTest):
    """test links of base*.html files"""

    def test_base1 (self):
        """test links of base1.html"""
        self.file_test("base1.html")

    def test_base2 (self):
        """test links of base2.html"""
        self.file_test("base2.html")

    def test_base3 (self):
        """test links of base3.html"""
        self.file_test("base3.html")


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBase))
    return suite

if __name__ == '__main__':
    unittest.main()
