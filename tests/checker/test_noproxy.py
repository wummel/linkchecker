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
Test proxy handling.
"""
import httpserver
from test.test_support import EnvironmentVarGuard

class TestProxy (httpserver.HttpServerTest):
    """Test no_proxy env var handling."""

    def test_noproxy (self):
        # set env vars
        with EnvironmentVarGuard() as env:
            env.set("http_proxy", "http://example.org:8877")
            env.set("no_proxy", "localhost:%d" % self.port)
            self.noproxy_test()

    def noproxy_test(self):
        # Test setting proxy and no_proxy env variable.
        url = self.get_url(u"favicon.ico")
        nurl = url
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Ignoring proxy setting `http://example.org:8877'.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=0)
