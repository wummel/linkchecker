# -*- coding: iso-8859-1 -*-
"""test news checking"""
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

import linkcheck.ftests
import linkcheck.url


class TestNews (linkcheck.ftests.StandardTest):
    """test nntp: and news: link checking"""

    needed_resources = ['network']

    def newstest (self, url, resultlines):
        fields = ['url', 'cachekey', 'realurl', 'warning', 'result', ]
        self.direct(url, resultlines, fields=fields)

    def test_news (self):
        """test news: link"""
        # news testing
        url = u"news:comp.os.linux.misc"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning No NNTP server specified, skipping this URL",
            "valid",
        ]
        self.newstest(url, resultlines)
        # no group
        url = u"news:"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning No NNTP server specified, skipping this URL",
            "valid",
        ]
        self.newstest(url, resultlines)

    def test_snews (self):
        """test snews: link"""
        url = u"snews:de.comp.os.unix.linux.misc"
        nurl = linkcheck.url.url_norm(url)
        resultlines = [
            "url %s" % url,
            "cache key %s" % nurl,
            "real url %s" % nurl,
            "warning Base URL is not properly normed. Normed url is %s." % nurl,
            "warning No NNTP server specified, skipping this URL",
            "valid",
        ]
        self.newstest(url, resultlines)

    def test_illegal (self):
        # illegal syntax
        url = u"news:§$%&/´`(§%"
        qurl = self.quote(url)
        resultlines = [
            "url %s" % url,
            "cache key %s" % qurl,
            "real url %s" % qurl,
            "warning Base URL is not properly normed. Normed url is %s." % qurl,
            "warning No NNTP server specified, skipping this URL",
            "valid",
        ]
        self.newstest(url, resultlines)

    def test_nntp (self):
        """nttp scheme with host"""
        url = u"nntp://news.yaako.com/comp.lang.python"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "valid",
        ]
        self.newstest(url, resultlines)

    def test_article_span (self):
        """article span"""
        url = u"nntp://news.yaako.com/comp.lang.python/1-5"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "valid",
        ]
        self.newstest(url, resultlines)
        url = u"news:comp.lang.python/1-5"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning No NNTP server specified, skipping this URL",
            "valid",
        ]
        self.newstest(url, resultlines)

    def test_host_no_group (self):
        """host but no group"""
        url = u"nntp://news.yaako.com/"
        resultlines = [
            "url %s" % url,
            "cache key %s" % url,
            "real url %s" % url,
            "warning No newsgroup specified in NNTP URL",
            "valid",
        ]
        self.newstest(url, resultlines)


def test_suite ():
    """build and return a TestSuite"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNews))
    return suite


if __name__ == '__main__':
    unittest.main()
