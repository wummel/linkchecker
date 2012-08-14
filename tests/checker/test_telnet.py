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
Test telnet checking.
"""
from . import LinkCheckTest


class TestTelnet (LinkCheckTest):
    """Test telnet: link checking."""

    def test_telnet_1 (self):
        url = u"telnet:"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key None",
            u"real url %s" % nurl,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_telnet_2 (self):
        url = u"telnet://www.example.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_telnet_3 (self):
        url = u"telnet://user@www.example.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_telnet_4 (self):
        url = u"telnet://user:pass@www.example.com"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)
