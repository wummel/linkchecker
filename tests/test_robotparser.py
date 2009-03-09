# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2009 Bastian Kleineidam
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
Test robots.txt parsing.
"""

import unittest
from tests import has_network
from nose import SkipTest
import linkcheck.robotparser2


class TestRobotParser (unittest.TestCase):
    """
    Test robots.txt parser (needs internet access).
    """

    def setUp (self):
        """
        Initialize self.rp as a robots.txt parser.
        """
        self.rp = linkcheck.robotparser2.RobotFileParser()

    def check (self, a, b):
        """
        Helper function comparing two results a and b.
        """
        if not b:
            ac = "access denied"
        else:
            ac = "access allowed"
        if a != b:
            self.fail("%s != %s (%s)" % (a, b, ac))

    def test_nonexisting_robots (self):
        """
        Test access of a non-existing robots.txt file.
        """
        if not has_network():
            raise SkipTest("no network available")
        # robots.txt that does not exist
        self.rp.set_url('http://www.lycos.com/robots.txt')
        self.rp.read()
        self.check(self.rp.can_fetch('Mozilla',
                                     'http://www.lycos.com/search'), True)

    def test_password_robots (self):
        # whole site is password-protected.
        if not has_network():
            raise SkipTest("no network available")
        self.rp.set_url('http://mueblesmoraleda.com/robots.txt')
        self.rp.read()
        self.check(self.rp.can_fetch("*",
                                     "http://mueblesmoraleda.com/"), False)
