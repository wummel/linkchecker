# -*- coding: iso-8859-1 -*-
"""test http checking"""
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
import os

import linkcheck.ftests.httptest


class TestHttp (linkcheck.ftests.httptest.HttpServerTest):
    """test http:// link checking"""

    def test_html (self):
        self.start_server()
        url = u"http://localhost:%d/linkcheck/ftests/data/http.html"%self.port
        resultlines = self.get_resultlines("http.html")
        try:
            self.direct(url, resultlines, recursionlevel=1)
        finally:
            self.stop_server()


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestHttp))
    return suite


if __name__ == '__main__':
    unittest.main()
