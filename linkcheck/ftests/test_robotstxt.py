# -*- coding: iso-8859-1 -*-
"""
Test HTML robots.txt parsing.
"""
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

import unittest
import os

import linkcheck.ftests


class TestRobotsTxt (linkcheck.ftests.StandardTest):
    """
    Test robots.txt directive parsing in HTML files.
    """

    def test_norobot (self):
        """
        Test links of norobot.html.
        """
        self.file_test("norobots.html")


def test_suite ():
    """
    Build and return a TestSuite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRobotsTxt))
    return suite


if __name__ == '__main__':
    unittest.main()
