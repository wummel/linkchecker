# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2009 Bastian Kleineidam
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
Test news checking.
"""
from tests import has_network
from nose import SkipTest
from . import LinkCheckTest


class TestHttps (LinkCheckTest):
    """
    Test https: link checking.
    """

    def test_https (self):
        if not has_network():
            raise SkipTest("no network available")
        url = u"https://www.amazon.de/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info Amazon servers block HTTP HEAD requests, using GET instead.",
            u"valid",
        ]
        self.direct(url, resultlines)
