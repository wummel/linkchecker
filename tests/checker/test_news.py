# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2010,2014 Bastian Kleineidam
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
import pytest
from tests import need_newsserver, limit_time
from . import LinkCheckTest

# Changes often, as servers tend to get invalid. Thus it is necessary
# to enable the has_newsserver() resource manually.
NNTP_SERVER = "news.uni-stuttgart.de"
# info string returned by news server
NNTP_INFO = u"200 news.uni-stuttgart.de InterNetNews NNRP server " \
            u"INN 2.5.2 ready (no posting)"
# Most free NNTP servers are slow, so don't waist a lot of time running those.
NNTP_TIMEOUT_SECS = 30

# disabled for now until some stable news server comes up
@pytest.mark.skipif("True")
class TestNews (LinkCheckTest):
    """Test nntp: and news: link checking."""

    def newstest (self, url, resultlines):
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
            u"warning No NNTP server was specified, skipping this URL.",
            u"valid",
        ]
        self.newstest(url, resultlines)

    @need_newsserver(NNTP_SERVER)
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

    @need_newsserver(NNTP_SERVER)
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

    @need_newsserver(NNTP_SERVER)
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
