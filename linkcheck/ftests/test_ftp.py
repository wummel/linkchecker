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

    needed_resources = ['network']

    def test_ftp (self):
        """test ftp link"""
        # ftp two slashes
        url = "ftp://ftp.debian.org/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_missing_slashes (self):
        """test ftp links with missing slashes"""
        # ftp one slash
        url = "ftp:/ftp.debian.org/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)
        # missing trailing slash
        url = "ftp://ftp.debian.org"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning Missing trailing directory slash in ftp url",
            "valid",
        ]
        self.direct(url, resultlines)
        # missing trailing dir slash
        url = "ftp://ftp.debian.org/debian"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning Missing trailing directory slash in ftp url",
            "valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_many_slashes (self):
        """test ftp links with too many slashes"""
        # ftp two dir slashes
        url = "ftp://ftp.debian.org//debian/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning Too many directory slashes",
            "valid",
        ]
        self.direct(url, resultlines)
        # ftp many dir slashes
        url = "ftp://ftp.debian.org////////debian/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning too many directory slashes",
            "valid",
        ]
        self.direct(url, resultlines)
        # ftp three slashes
        url = "ftp:///ftp.debian.org/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFtp))
    return suite


if __name__ == '__main__':
    unittest.main()
