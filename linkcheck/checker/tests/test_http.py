# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2008 Bastian Kleineidam
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
Test http checking.
"""

import unittest
import os
import re

import httptest


class TestHttp (httptest.HttpServerTest):
    """
    Test http:// link checking.
    """

    def test_html (self):
        try:
            self.start_server(handler=CookieRedirectHttpRequestHandler)
            url = u"http://localhost:%d/linkcheck/checker/tests/data/" \
                  u"http.html" % self.port
            resultlines = self.get_resultlines("http.html")
            self.direct(url, resultlines, recursionlevel=1)
            self.redirect1_http_test()
            self.redirect2_http_test()
            self.robots_txt_test()
            self.robots_txt2_test()
            self.noproxyfor_test()
            self.swf_test()
        finally:
            self.stop_server()

    def test_redirect (self):
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
            u"real url %s" % rurl,
            u"info Redirected to %s." % rurl.replace('http:', 'https:'),
            u"warning Redirection to different URL type encountered; the " \
            u"original URL was %r." % url,
            u"valid",
            u"url %s" % rurl,
            u"cache key %s" % rurl,
            u"real url %s" % rurl,
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
            u"info Redirected to %s." % rurl,
            u"error",
        ]
        self.direct(url, resultlines, recursionlevel=0)

    def redirect2_http_test (self):
        url = u"http://localhost:%d/linkcheck/checker/tests/data/redirect.html" % \
              self.port
        nurl = url
        rurl = url.replace("redirect", "newurl")
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % rurl,
            u"info Redirected to %s." % rurl,
            u"valid",
            u"url newurl.html (cached)",
            u"cache key %s" % rurl,
            u"real url %s" % rurl,
            u"name Recursive Redirect",
            u"info Redirected to %s." % rurl,
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=99)

    def robots_txt_test (self):
        url = u"http://localhost:%d/robots.txt" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=5)

    def robots_txt2_test (self):
        url = u"http://localhost:%d/secret" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"warning Access denied by robots.txt, checked only syntax.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=5)

    def noproxyfor_test (self):
        """
        Test setting proxy and --no-proxy-for option.
        """
        os.environ["http_proxy"] = "http://example.org:8877"
        confargs = {"noproxyfor": [re.compile("localhost")]}
        url = u"http://localhost:%d/linkcheck/checker/tests/data/http.html" % \
              self.port
        nurl = url
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"info Ignoring proxy setting 'example.org:8877'",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=0,
                    confargs=confargs)
        del os.environ["http_proxy"]

    def swf_test (self):
        url = u"http://localhost:%d/linkcheck/checker/tests/data/" \
              u"test.swf" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
            u"url http://www.example.org/",
            u"cache key http://www.example.org/",
            u"real url http://www.example.org/",
            u"warning Access denied by robots.txt, checked only syntax.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=1)


def get_cookie (maxage=2000):
    data = (
        ("Comment", "justatest"),
        ("Max-Age", "%d" % maxage),
        ("Path", "/"),
        ("Version", "1"),
        ("Foo", "Bar"),
    )
    return "; ".join('%s="%s"' % (key, value) for key, value in data)


class CookieRedirectHttpRequestHandler (httptest.NoQueryHttpRequestHandler):
    """
    Handler redirecting certain requests, and setting cookies.
    """

    def end_headers (self):
        """
        Send cookie before ending headers.
        """
        self.send_header("Set-Cookie", get_cookie())
        self.send_header("Set-Cookie", get_cookie(maxage=0))
        super(CookieRedirectHttpRequestHandler, self).end_headers()

    def redirect (self):
        """
        Redirect request.
        """
        path = self.path.replace("redirect", "newurl")
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET (self):
        """
        Removes query part of GET request.
        """
        if "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_GET()

    def do_HEAD (self):
        if "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_HEAD()

class RedirectHttpsRequestHandler (CookieRedirectHttpRequestHandler):

    def redirect (self):
        """
        Redirect request.
        """
        path = self.path.replace("redirect", "newurl")
        port = self.server.server_address[1]
        url = "https://localhost:%d%s" % (port, path)
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

def test_suite ():
    """
    Build and return a TestSuite.
    """
    return unittest.makeSuite(TestHttp)


if __name__ == '__main__':
    unittest.main()
