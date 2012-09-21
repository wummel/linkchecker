# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2012 Bastian Kleineidam
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
Test http checking.
"""
from .httpserver import HttpServerTest, CookieRedirectHttpRequestHandler

class TestHttp (HttpServerTest):
    """Test http:// link checking."""

    def test_html (self):
        try:
            self.start_server(handler=CookieRedirectHttpRequestHandler)
            url = u"http://localhost:%d/tests/checker/data/" \
                  u"http.html" % self.port
            resultlines = self.get_resultlines("http.html")
            self.direct(url, resultlines, recursionlevel=1)
            url = u"http://localhost:%d/tests/checker/data/" \
                  u"http.xhtml" % self.port
            resultlines = self.get_resultlines("http.xhtml")
            self.direct(url, resultlines, recursionlevel=1)
        finally:
            self.stop_server()
