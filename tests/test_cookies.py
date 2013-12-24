# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2013 Bastian Kleineidam
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
Test cookie routines.
"""

import unittest
import linkcheck.cookies


class TestCookies (unittest.TestCase):
    """Test cookie routines."""

    def test_netscape_cookie1 (self):
        data = (
            ("Foo", "Bar"),
            ("Comment", "justatest"),
            ("Max-Age", "1000"),
            ("Path", "/"),
            ("Version", "1"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.NetscapeCookie(value, scheme, host, path)
        self.assertTrue(cookie.check_expired())
        self.assertTrue(cookie.is_valid_for("http", host, 80, "/"))
        self.assertTrue(cookie.is_valid_for("https", host, 443, "/a"))

    def test_netscape_cookie2 (self):
        data = (
            ("Foo", "Bar"),
            ("Comment", "justatest"),
            ("Max-Age", "0"),
            ("Path", "/"),
            ("Version", "1"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.NetscapeCookie(value, scheme, host, path)
        self.assertTrue(cookie.is_expired())

    def test_netscape_cookie3 (self):
        # invalid port
        data = (
            ("Foo", "Bar"),
            ("Port", "hul,la"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        self.assertRaises(linkcheck.cookies.CookieError,
                 linkcheck.cookies.NetscapeCookie, value, scheme, host, path)

    def test_netscape_cookie4 (self):
        data = (
            ("Foo", "Bar"),
            ("Domain", "localhost"),
            ("Port", "100,555,76"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.NetscapeCookie(value, scheme, host, path)
        self.assertTrue(cookie.is_valid_for("http", host, 100, "/"))

    def test_netscape_cookie5 (self):
        data = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Expires", "Wed, 12-Dec-2001 19:27:57 GMT"),
            ("Path", "/"),
        )
        # note: values are without quotes
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        scheme = "http"
        host = "example.org"
        path = "/"
        cookie = linkcheck.cookies.NetscapeCookie(value, scheme, host, path)
        self.assertTrue(cookie.is_expired())

    def test_netscape_cookie6 (self):
        data = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        # note: values are without quotes
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        scheme = "http"
        host = "example.org"
        path = "/"
        cookie = linkcheck.cookies.NetscapeCookie(value, scheme, host, path)
        self.assertTrue(cookie.is_valid_for("http", "example.org", 80, "/"))
        self.assertTrue(cookie.is_valid_for("http", "www.example.org", 80, "/"))
        self.assertFalse(cookie.is_valid_for("http", "www.b.example.org", 80, "/"))

    def test_netscape_cookie7 (self):
        data1 = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        data2 = (
            ("FOO", "Baz"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        data3 = (
            ("FOOl", "Baz"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        # note: values are without quotes
        value1 = "; ".join('%s=%s' % (key, value) for key, value in data1)
        value2 = "; ".join('%s=%s' % (key, value) for key, value in data2)
        value3 = "; ".join('%s=%s' % (key, value) for key, value in data3)
        scheme = "http"
        host = "example.org"
        path = "/"
        cookie1 = linkcheck.cookies.NetscapeCookie(value1, scheme, host, path)
        cookie2 = linkcheck.cookies.NetscapeCookie(value2, scheme, host, path)
        cookie3 = linkcheck.cookies.NetscapeCookie(value3, scheme, host, path)
        self.assertEqual(cookie1, cookie2)
        self.assertNotEqual(cookie1, cookie3)
        self.assertNotEqual(cookie2, cookie3)

    def test_netscape_cookie8 (self):
        value = ""
        scheme = "http"
        host = "localhost"
        path = "/"
        self.assertRaises(linkcheck.cookies.CookieError,
                 linkcheck.cookies.NetscapeCookie, value, scheme, host, path)

    def test_netscape_cookie9 (self):
        # illegal expiration date
        data = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Expires", "Thu, 08-Oct-3697739 18:36:07 GMT"),
            ("Path", "/"),
        )
        # note: values are without quotes
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        scheme = "http"
        host = "example.org"
        path = "/"
        self.assertRaises(linkcheck.cookies.CookieError,
                 linkcheck.cookies.NetscapeCookie, value, scheme, host, path)

    def test_rfc_cookie1 (self):
        data = (
            ("Foo", "Bar"),
            ("Comment", "justatest"),
            ("Max-Age", "1000"),
            ("Path", "/"),
            ("Version", "1"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.Rfc2965Cookie(value, scheme, host, path)
        self.assertTrue(cookie.check_expired())
        self.assertTrue(cookie.is_valid_for("http", host, 80, "/"))
        self.assertTrue(cookie.is_valid_for("https", host, 443, "/a"))

    def test_rfc_cookie2 (self):
        data = (
            ("Foo", "Bar"),
            ("Comment", "justatest"),
            ("Max-Age", "0"),
            ("Path", "/"),
            ("Version", "1"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.Rfc2965Cookie(value, scheme, host, path)
        self.assertTrue(cookie.is_expired())

    def test_rfc_cookie3 (self):
        # invalid port
        data = (
            ("Foo", "Bar"),
            ("Port", "hul,la"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        self.assertRaises(linkcheck.cookies.CookieError,
                 linkcheck.cookies.Rfc2965Cookie, value, scheme, host, path)

    def test_rfc_cookie4 (self):
        data = (
            ("Foo", "Bar"),
            ("Port", "100,555,76"),
        )
        value = "; ".join('%s="%s"' % (key, value) for key, value in data)
        scheme = "http"
        host = "localhost"
        path = "/"
        cookie = linkcheck.cookies.Rfc2965Cookie(value, scheme, host, path)
        self.assertTrue(cookie.is_valid_for("http", host, 100, "/"))

    def test_rfc_cookie5 (self):
        data1 = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        data2 = (
            ("FOO", "Baz"),
            ("Domain", "EXAMPLE.org"),
            ("Path", "/"),
        )
        data3 = (
            ("FOOl", "Baz"),
            ("Domain", "EXAMPLE.org"),
            ("Path", "/"),
        )
        # note: values are without quotes
        value1 = "; ".join('%s=%s' % (key, value) for key, value in data1)
        value2 = "; ".join('%s=%s' % (key, value) for key, value in data2)
        value3 = "; ".join('%s=%s' % (key, value) for key, value in data3)
        scheme = "http"
        host = "example.org"
        path = "/"
        cookie1 = linkcheck.cookies.Rfc2965Cookie(value1, scheme, host, path)
        cookie2 = linkcheck.cookies.Rfc2965Cookie(value2, scheme, host, path)
        cookie3 = linkcheck.cookies.Rfc2965Cookie(value3, scheme, host, path)
        self.assertEqual(cookie1, cookie2)
        self.assertNotEqual(cookie1, cookie3)
        self.assertNotEqual(cookie2, cookie3)

    def test_cookie_parse1 (self):
        lines = [
            'Host: example.org',
            'Path: /hello',
            'Set-cookie: ID="smee"',
            'Set-cookie: spam="egg"',
        ]
        from_headers = linkcheck.cookies.from_headers
        headers, scheme, host, path = from_headers("\r\n".join(lines))
        self.assertEqual(scheme, "http")
        self.assertEqual(host, "example.org")
        self.assertEqual(path, "/hello")
        self.assertEqual(len(headers.headers), 4)

    def test_cookie_parse2 (self):
        lines = [
            'Scheme: https',
            'Host: example.org',
            'Set-cookie: baggage="elitist"; comment="hologram"',
        ]
        from_headers = linkcheck.cookies.from_headers
        headers, scheme, host, path = from_headers("\r\n".join(lines))
        self.assertEqual(scheme, "https")
        self.assertEqual(host, "example.org")
        self.assertEqual(path, "/")
        self.assertEqual(len(headers.headers), 3)

    def test_cookie_parse3 (self):
        lines = [
            'Scheme: https',
        ]
        from_headers = linkcheck.cookies.from_headers
        self.assertRaises(ValueError, from_headers, "\r\n".join(lines))

    def test_cookie_parse4 (self):
        lines = [
            ' Host: imaweevil.org',
            'Set-cookie: baggage="elitist"; comment="hologram"',
        ]
        from_headers = linkcheck.cookies.from_headers
        self.assertRaises(ValueError, from_headers, "\r\n".join(lines))
