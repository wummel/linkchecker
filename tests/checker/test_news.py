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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Test news checking.
"""
from tests import has_network, limit_time, memoized
from nose import SkipTest
from . import LinkCheckTest

# Changes often, as servers tend to get invalid. Thus it is necessary
# to enable the has_newsserver() resource manually.
NNTP_SERVER = "freenews.netfront.net"
# info string returned by news server
NNTP_INFO = u"200 news.netfront.net InterNetNews NNRP server INN 2.4.6 (20090304 snapshot) ready (posting ok)."
# Most free NNTP servers are slow, so don't waist a lot of time running those.
NNTP_TIMEOUT_SECS = 8


@memoized
def has_newsserver ():
    try:
        nntp = nntplib.NNTP(NNTP_SERVER, usenetrc=False)
        nntp.close()
        return True
    except :
        return False


class TestNews (LinkCheckTest):
    """Test nntp: and news: link checking."""

    def newstest (self, url, resultlines):
        if not has_network():
            raise SkipTest("no network available")
        if not has_newsserver():
            raise SkipTest("no newswerver available")
        self.direct(url, resultlines)

    def test_news_without_host (self):
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

    def test_snews_with_group (self):
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

    def test_illegal_syntax (self):
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

    @limit_time(NNTP_TIMEOUT_SECS, skip=True)
    def test_nntp_with_host (self):
        url = u"nntp://%s/comp.lang.python" % NNTP_SERVER
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info %s" % NNTP_INFO,
            u"info News group comp.lang.python found.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    @limit_time(NNTP_TIMEOUT_SECS, skip=True)
    def test_article_span (self):
        url = u"nntp://%s/comp.lang.python/1-5" % NNTP_SERVER
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info %s" % NNTP_INFO,
            u"info News group comp.lang.python found.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    def test_article_span_no_host (self):
        url = u"news:comp.lang.python/1-5"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    @limit_time(NNTP_TIMEOUT_SECS, skip=True)
    def test_host_no_group (self):
        url = u"nntp://%s/" % NNTP_SERVER
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info %s" % NNTP_INFO,
            u"warning No newsgroup specified in NNTP URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)
