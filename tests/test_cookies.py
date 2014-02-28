# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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

    def test_cookie_parse_multiple_headers (self):
        lines = [
            'Host: example.org',
            'Path: /hello',
            'Set-cookie: ID="smee"',
            'Set-cookie: spam="egg"',
        ]
        from_headers = linkcheck.cookies.from_headers
        cookies = from_headers("\r\n".join(lines))
        self.assertEqual(len(cookies), 2)
        for cookie in cookies:
            self.assertEqual(cookie.domain, "example.org")
            self.assertEqual(cookie.path, "/hello")
        self.assertEqual(cookies[0].name, 'ID')
        self.assertEqual(cookies[0].value, 'smee')
        self.assertEqual(cookies[1].name, 'spam')
        self.assertEqual(cookies[1].value, 'egg')

    def test_cookie_parse_multiple_values (self):
        lines = [
            'Host: example.org',
            'Set-cookie: baggage="elitist"; comment="hologram"',
        ]
        from_headers = linkcheck.cookies.from_headers
        cookies = from_headers("\r\n".join(lines))
        self.assertEqual(len(cookies), 2)
        for cookie in cookies:
            self.assertEqual(cookie.domain, "example.org")
            self.assertEqual(cookie.path, "/")
        self.assertEqual(cookies[0].name, 'baggage')
        self.assertEqual(cookies[0].value, 'elitist')
        self.assertEqual(cookies[1].name, 'comment')
        self.assertEqual(cookies[1].value, 'hologram')

    def test_cookie_parse_error (self):
        lines = [
            ' Host: imaweevil.org',
            'Set-cookie: baggage="elitist"; comment="hologram"',
        ]
        from_headers = linkcheck.cookies.from_headers
        self.assertRaises(ValueError, from_headers, "\r\n".join(lines))
