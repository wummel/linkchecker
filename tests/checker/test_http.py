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
import os
import sys
from .httpserver import HttpServerTest, NoQueryHttpRequestHandler
from linkcheck.network import iputil

class TestHttp (HttpServerTest):
    """Test http:// link checking."""

    def test_html (self):
        try:
            self.start_server(handler=CookieRedirectHttpRequestHandler)
            url = u"http://localhost:%d/tests/checker/data/" \
                  u"http.html" % self.port
            resultlines = self.get_resultlines("http.html")
            self.direct(url, resultlines, recursionlevel=1)
            url = u"http://localhost:%d/tests/checker/data/" \
                  u"http.xhtml" % self.port
            resultlines = self.get_resultlines("http.xhtml")
            self.direct(url, resultlines, recursionlevel=1)
            self.redirect1_http_test()
            self.redirect2_http_test()
            self.redirect3_http_test()
            self.redirect4_http_test()
            self.redirect5_http_test()
            self.robots_txt_test()
            self.robots_txt2_test()
            self.swf_test()
            self.obfuscate_test()
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
            u"warning Access denied by robots.txt, skipping content checks.",
            u"error",
        ]
        self.direct(url, resultlines, recursionlevel=5)

    def swf_test (self):
        url = u"http://localhost:%d/tests/checker/data/test.swf" % self.port
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"info 1 URL parsed.",
            u"valid",
            u"url http://www.example.org/",
            u"cache key http://www.example.org/",
            u"real url http://www.iana.org/domains/example/",
            u"info Redirected to `http://www.iana.org/domains/example/'.",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=1)

    def obfuscate_test (self):
        if os.name != "posix" or sys.platform != 'linux2':
            return
        host = "www.google.de"
        ip = iputil.resolve_host(host).pop()
        url = u"http://%s/" % iputil.obfuscate_ip(ip)
        rurl = u"http://%s/" % host
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % rurl,
            u"info Redirected to `%s'." % rurl,
            u"warning URL %s has obfuscated IP address %s" % (url, ip),
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=0)

def get_cookie (maxage=2000):
    data = (
        ("Comment", "justatest"),
        ("Max-Age", "%d" % maxage),
        ("Path", "/"),
        ("Version", "1"),
        ("Foo", "Bar"),
    )
    return "; ".join('%s="%s"' % (key, value) for key, value in data)


class CookieRedirectHttpRequestHandler (NoQueryHttpRequestHandler):
    """Handler redirecting certain requests, and setting cookies."""

    def end_headers (self):
        """Send cookie before ending headers."""
        self.send_header("Set-Cookie", get_cookie())
        self.send_header("Set-Cookie", get_cookie(maxage=0))
        super(CookieRedirectHttpRequestHandler, self).end_headers()

    def redirect (self):
        """Redirect request."""
        path = self.path.replace("redirect", "newurl")
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def redirect_newhost (self):
        """Redirect request to a new host."""
        path = "http://www.example.com/"
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def redirect_newscheme (self):
        """Redirect request to a new scheme."""
        if "file" in self.path:
            path = "file:README"
        else:
            path = "ftp://example.com/"
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET (self):
        """Handle redirections for GET."""
        if "redirect_newscheme" in self.path:
            self.redirect_newscheme()
        elif "redirect_newhost" in self.path:
            self.redirect_newhost()
        elif "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_GET()

    def do_HEAD (self):
        """Handle redirections for HEAD."""
        if "redirect_newscheme" in self.path:
            self.redirect_newscheme()
        elif "redirect_newhost" in self.path:
            self.redirect_newhost()
        elif "redirect" in self.path:
            self.redirect()
        else:
            super(CookieRedirectHttpRequestHandler, self).do_HEAD()


class RedirectHttpsRequestHandler (CookieRedirectHttpRequestHandler):

    def redirect (self):
        """Redirect request."""
        path = self.path.replace("redirect", "newurl")
        port = self.server.server_address[1]
        url = "https://localhost:%d%s" % (port, path)
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()
