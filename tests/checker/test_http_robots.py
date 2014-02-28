# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
from .httpserver import HttpServerTest

class TestHttpRobots (HttpServerTest):
    """Test robots.txt link checking behaviour."""

    def test_html (self):
        self.robots_txt_test()
        self.robots_txt2_test()

    def robots_txt_test (self):
        url = u"http://localhost:%d/robots.txt" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=5)

    def robots_txt2_test (self):
        url = u"http://localhost:%d/secret" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info Access denied by robots.txt, checked only syntax.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=5)
