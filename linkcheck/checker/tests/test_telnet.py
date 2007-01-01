# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2007 Bastian Kleineidam
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
Test telnet checking.
"""

import unittest

import linkcheck.checker.tests


class TestTelnet (linkcheck.checker.tests.LinkCheckTest):
    """
    Test telnet: link checking.
    """

    def test_telnet (self):
        url = u"telnet:"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
        url = u"telnet://www.imarealdoofus.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)
        url = u"telnet://user@www.imarealdoofus.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)
        url = u"telnet://user:pass@www.imarealdoofus.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestTelnet)


if __name__ == '__main__':
    unittest.main()
