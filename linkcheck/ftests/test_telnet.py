# -*- coding: iso-8859-1 -*-
"""test telnet checking"""
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
        nurl = linkcheck.url.url_norm(url)
        resultlines = [
            "url %r" % url,
            "cache key %s" % nurl,
            "real url %s" % nurl,
            "warning Base URL is not properly normed. Normed url is %r." % nurl,
            "error",
        ]
        self.direct(url, resultlines)
        url = "telnet://www.imadoofus.com"
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)
        url = "telnet://user@www.imadoofus.com"
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)
        url = "telnet://user:pass@www.imadoofus.com"
        resultlines = [
            "url %r" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "error",
        ]
        self.direct(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTelnet))
    return suite


if __name__ == '__main__':
    unittest.main()
