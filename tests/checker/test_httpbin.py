# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
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
Test http stuff with httpbin.org.
"""
import re
from . import LinkCheckTest


def get_httpbin_url(path):
    """Get httpbin URL. Note that this also could be a local
    httpbin installation, but right now this uses the official site."""
    return u"http://httpbin.org%s" % path


class TestHttpbin(LinkCheckTest):
    """Test http:// link redirection checking."""

    def test_http_link(self):
        linkurl = u"http://www.example.com"
        nlinkurl = self.norm(linkurl)
        url = get_httpbin_url(u"/response-headers?Link=<%s>;rel=previous" % linkurl)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
            u"url %s" % linkurl,
            u"cache key %s" % nlinkurl,
            u"real url %s" % nlinkurl,
            u"name Link: header previous",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=1)

    def test_basic_auth(self):
        user = u"testuser"
        password = u"testpassword"
        url = get_httpbin_url(u"/basic-auth/%s/%s" % (user, password))
        nurl = self.norm(url)
        entry = dict(
            user=user,
            password=password,
            pattern=re.compile(r'.*'),
        )
        confargs = dict(authentication=[entry])
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines, confargs=confargs)

    def test_http_refresh_header(self):
        linkurl = u"http://www.example.com"
        nlinkurl = self.norm(linkurl)
        url = get_httpbin_url(u"/response-headers?Refresh=5;url=%s" % linkurl)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
            u"url %s" % linkurl,
            u"cache key %s" % nlinkurl,
            u"real url %s" % nlinkurl,
            u"name Refresh: header",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=1)

    def test_http_content_location_header(self):
        linkurl = u"http://www.example.com"
        nlinkurl = self.norm(linkurl)
        url = get_httpbin_url(u"/response-headers?Content-Location=%s" % linkurl)
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
            u"url %s" % linkurl,
            u"cache key %s" % nlinkurl,
            u"real url %s" % nlinkurl,
            u"name Content-Location: header",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=1)
