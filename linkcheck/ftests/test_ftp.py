# -*- coding: iso-8859-1 -*-
"""test ftp checking"""
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


class TestFtp (linkcheck.ftests.StandardTest):
    """test ftp: link checking"""

    def test_ftp (self):
        """test some ftp links"""
        # ftp one slash
        url = "ftp:/ftp.debian.org/"
        resultlines = ["url %s" % url, "error"]
        self.direct(url, resultlines)
        # ftp two slashes
        url = "ftp://ftp.debian.org/"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        # ftp two dir slashes
        url = "ftp://ftp.debian.org//debian/"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        # missing trailing dir slash
        url = "ftp://ftp.debian.org/debian"
        resultlines = [
            "url %s" % url,
            "warning Missing trailing directory slash in ftp url",
            "valid",
        ]
        self.direct(url, resultlines)
        # ftp many dir slashes
        url = "ftp://ftp.debian.org////////debian/"
        resultlines = ["url %s" % url, "valid"]
        self.direct(url, resultlines)
        # ftp three slashes
        url = "ftp:///ftp.debian.org/"
        resultlines = ["url %s" % url, "error"]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFtp))
    return suite


if __name__ == '__main__':
    unittest.main()
