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

    def __init__(self, methodName='runTest'):
        super(TestHttp, self).__init__(methodName=methodName)
        self.handler = CookieRedirectHttpRequestHandler

    def test_html (self):
        confargs = dict(recursionlevel=1)
        self.file_test("http.html", confargs=confargs)
        self.file_test("http_lowercase.html", confargs=confargs)
        self.file_test("http_quotes.html", confargs=confargs)
        self.file_test("http_slash.html", confargs=confargs)
        self.file_test("http.xhtml", confargs=confargs)

