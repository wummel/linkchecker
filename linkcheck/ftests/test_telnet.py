# -*- coding: iso-8859-1 -*-
"""test news checking"""
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


class TestTelnet (linkcheck.ftests.StandardTest):
    """test telnet: link checking"""

    def test_telnet (self):
        url = "telnet:"
        resultlines = ["url %s" % url, "error"]
        self.direct(url, resultlines)
        url = "telnet://swindon.city.ac.uk"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        url = "telnet://user@swindon.city.ac.uk"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        url = "telnet://user:password@swindon.city.ac.uk"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTelnet))
    return suite


if __name__ == '__main__':
    unittest.main()
