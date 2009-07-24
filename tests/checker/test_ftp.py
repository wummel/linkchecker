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
Test ftp checking.
"""
from tests import has_network
from nose import SkipTest
from . import LinkCheckTest


class TestFtp (LinkCheckTest):
    """
    Test ftp: link checking.
    """

    def test_ftp (self):
        # ftp two slashes
        if not has_network():
            raise SkipTest("no network available")
        url = u"ftp://ftp.de.debian.org/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_slashes (self):
        # ftp one slash
        if not has_network():
            raise SkipTest("no network available")
        url = u"ftp:/ftp.de.debian.org/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"error",
        ]
        self.direct(url, resultlines)
        # missing path
        url = u"ftp://ftp.de.debian.org"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # missing trailing dir slash
        url = u"ftp://ftp.de.debian.org/debian"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s/" % nurl,
            u"warning Missing trailing directory slash in ftp url.",
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_ftp_many_slashes (self):
        # ftp two dir slashes
        if not has_network():
            raise SkipTest("no network available")
        url = u"ftp://ftp.de.debian.org//debian/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp many dir slashes
        url = u"ftp://ftp.de.debian.org////////debian/"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)
        # ftp three slashes
        url = u"ftp:///ftp.de.debian.org/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"error",
        ]
        self.direct(url, resultlines)
