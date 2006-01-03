# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2006 Bastian Kleineidam
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
"""
Test news checking.
"""

import unittest

import linkcheck.checker.tests
import linkcheck.url


class TestNews (linkcheck.checker.tests.LinkCheckTest):
    """
    Test nntp: and news: link checking.
    """

    needed_resources = ['network']

    def newstest (self, url, resultlines):
        fields = ['url', 'cachekey', 'realurl', 'warning', 'result', ]
        self.direct(url, resultlines, fields=fields)

    def test_news (self):
        """
        Test news: link.
        """
        # news testing
        url = u"news:comp.os.linux.misc"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)
        # no group
        url = u"news:"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_snews (self):
        """
        Test snews: link.
        """
        url = u"snews:de.comp.os.unix.linux.misc"
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % nurl,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_illegal (self):
        # illegal syntax
        url = u"news:§$%&/´`(§%"
        qurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % qurl,
            u"real url %s" % qurl,
            u"warning Base URL is not properly normed. Normed URL is %s." % qurl,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_nntp (self):
        """
        Nttp scheme with host.
        """
        url = u"nntp://news.yaako.com/comp.lang.python"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info News group comp.lang.python found.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_article_span (self):
        """
        Article span.
        """
        url = u"nntp://news.yaako.com/comp.lang.python/1-5"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info News group comp.lang.python found.",
            u"valid",
        ]
        self.newstest(url, resultlines)
        url = u"news:comp.lang.python/1-5"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_host_no_group (self):
        """
        Host but no group.
        """
        url = u"nntp://news.yaako.com/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning No newsgroup specified in NNTP URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)


def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestNews)


if __name__ == '__main__':
    unittest.main()
