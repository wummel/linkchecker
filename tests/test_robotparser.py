# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Test robots.txt parsing.
"""

import unittest
from tests import need_network
from linkcheck import configuration, robotparser2


class TestRobotParser (unittest.TestCase):
    """
    Test robots.txt parser (needs internet access).
    """

    def setUp (self):
        """Initialize self.rp as a robots.txt parser."""
        self.rp = robotparser2.RobotFileParser()

    def check (self, a, b):
        """Helper function comparing two results a and b."""
        if not b:
            ac = "access denied"
        else:
            ac = "access allowed"
        if a != b:
            self.fail("%s != %s (%s)" % (a, b, ac))

    @need_network
    def test_nonexisting_robots (self):
        # robots.txt that does not exist
        self.rp.set_url('http://www.lycos.com/robots.txt')
        self.rp.read()
        self.check(self.rp.can_fetch(configuration.UserAgent,
                                     'http://www.lycos.com/search'), True)

    @need_network
    def test_disallowed_robots (self):
        self.rp.set_url('http://google.com/robots.txt')
        self.rp.read()
        self.check(self.rp.can_fetch(configuration.UserAgent,
                                     "http://google.com/search"), False)
