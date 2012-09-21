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
Test http checking.
"""
from .httpserver import HttpServerTest, CookieRedirectHttpRequestHandler

class TestHttpRedirect (HttpServerTest):
    """Test http:// link redirection checking."""

    def test_html (self):
        try:
            self.start_server(handler=CookieRedirectHttpRequestHandler)
            self.redirect1_http_test()
            self.redirect2_http_test()
            self.redirect3_http_test()
            self.redirect4_http_test()
            self.redirect5_http_test()
        finally:
            self.stop_server()

    def _test_redirect (self):
        try:
            self.start_server(handler=RedirectHttpsRequestHandler)
            self.redirect_https_test()
        finally:
            self.stop_server()

    def redirect_https_test (self):
        url = u"http://localhost:%d/redirect1" % self.port
        nurl = url
        rurl = u"https://localhost:%d/newurl1" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % url,
            u"info Redirected to `%s'." % rurl.replace('http:', 'https:'),
            u"error",
        ]
        self.direct(url, resultlines, recursionlevel=0)

    def redirect1_http_test (self):
        url = u"http://localhost:%d/redirect1" % self.port
        nurl = url
        rurl = url.replace("redirect", "newurl")
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % rurl,
            u"info Redirected to `%s'." % rurl,
            u"error",
        ]
        self.direct(url, resultlines, recursionlevel=0)

    def redirect2_http_test (self):
        url = u"http://localhost:%d/tests/checker/data/redirect.html" % \
              self.port
        nurl = url
        rurl = url.replace("redirect", "newurl")
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % rurl,
            u"info Redirected to `%s'." % rurl,
            u"info 1 URL parsed.",
            u"valid",
            u"url newurl.html (cached)",
            u"cache key %s" % rurl,
            u"real url %s" % rurl,
            u"name Recursive Redirect",
            u"info Redirected to `%s'." % rurl,
            u"info 1 URL parsed.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=99)

    def redirect3_http_test (self):
        url = u"http://localhost:%d/tests/checker/data/redir.html" % self.port
        resultlines = self.get_resultlines("redir.html")
        self.direct(url, resultlines, recursionlevel=1)

    def redirect4_http_test (self):
        url = u"http://localhost:%d/redirect_newscheme_ftp" % self.port
        nurl = url
        rurl = u"ftp://example.com/"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Redirected to `%s'." % rurl,
            u"warning Redirection to URL `%s' with different scheme found; the original URL was `%s'." % (rurl, nurl),
            u"valid",
            u"url %s" % rurl,
            u"cache key %s" % rurl,
            u"real url %s" % rurl,
            u"error",
        ]
        self.direct(url, resultlines, recursionlevel=99)

    def redirect5_http_test (self):
        url = u"http://localhost:%d/redirect_newscheme_file" % self.port
        nurl = url
        rurl = u"file:README"
        rnurl = u"file:///README"
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Redirected to `%s'." % rurl,
            u"warning Redirection to url `%s' is not allowed." % rnurl,
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=99)


class RedirectHttpsRequestHandler (CookieRedirectHttpRequestHandler):

    def redirect (self):
        """Redirect request."""
        path = self.path.replace("redirect", "newurl")
        port = self.server.server_address[1]
        url = "https://localhost:%d%s" % (port, path)
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()
