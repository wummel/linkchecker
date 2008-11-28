# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2008 Bastian Kleineidam
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
Test news checking.
"""

import unittest
from . import LinkCheckTest


class TestHttps (LinkCheckTest):
    """
    Test https: link checking.
    """

    needed_resources = ['network']

    def test_https (self):
        """
        Test some https links.
        """
        url = u"https://www.amazon.de/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info Amazon servers block HTTP HEAD requests, using GET instead.",
            u"valid",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestHttps)


if __name__ == '__main__':
    unittest.main()
