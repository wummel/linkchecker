# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Bastian Kleineidam
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
Test cookie jar caching routines.
"""

import unittest
import httplib
from StringIO import StringIO
import linkcheck.cache.cookie

def get_headers (name, value):
    """Return HTTP header object with given name and value."""
    data = "%s: %s" % (name, value)
    return httplib.HTTPMessage(StringIO(data))


class TestCookieJar (unittest.TestCase):
    """Test cookie jar routines."""

    def test_cookie_cache1 (self):
        scheme = "http"
        host = "example.org"
        path = "/"
        jar = linkcheck.cache.cookie.CookieJar()
        data = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 1)
        # add updated cookie
        data = (
            ("FOO", "Baz"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 1)
        # remove cookie
        data = (
            ("FOO", "Baz"),
            ("Domain", "example.org"),
            ("Path", "/"),
            ("Max-Age", "0"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 0)

    def test_cookie_cache2 (self):
        scheme = "http"
        host = "example.org"
        path = "/"
        jar = linkcheck.cache.cookie.CookieJar()
        data = (
            ("Foo", "Bar"),
            ("Domain", "example.org"),
            ("Path", "/"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie2', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 1)
        # add updated cookie
        data = (
            ("Foo", "Baz"),
            ("Domain", "EXAMPLE.org"),
            ("Path", "/"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie2', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 1)
        # remove cookie
        data = (
            ("FOO", "Baz"),
            ("Domain", "example.org"),
            ("Path", "/"),
            ("Max-Age", "0"),
        )
        value = "; ".join('%s=%s' % (key, value) for key, value in data)
        headers = get_headers('Set-Cookie2', value)
        jar.add(headers, scheme, host, path)
        self.assertEqual(len(jar.cache[host]), 0)
