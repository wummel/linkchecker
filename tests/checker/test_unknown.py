# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
Test checking of unknown URLs.
"""
from . import LinkCheckTest


class TestUnknown (LinkCheckTest):
    """Test unknown URL scheme checking."""

    def test_skype (self):
        url = u"skype:"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Skype URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_irc (self):
        url = u"irc://example.org"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Irc URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"ircs://example.org"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Ircs URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_steam (self):
        url = u"steam://connect/example.org"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Steam URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_feed (self):
        url = u"feed:https://example.com/entries.atom"
        nurl = u"feed:https%3A/example.com/entries.atom"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Feed URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)
        url = u"feed://example.com/entries.atom"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Feed URL ignored.",
            u"valid",
        ]
        self.direct(url, resultlines)
