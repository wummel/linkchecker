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
Test address info caching.
"""
import unittest
import socket
from linkcheck import LinkCheckerError
from linkcheck.cache.addrinfo import getaddrinfo

class TestAddrinfoCache (unittest.TestCase):
    """Test address info caching."""

    def test_addrinfo_cache1 (self):
        # pure ascii hostname with >63 chars
        host = u"a"*64
        port = 80
        # must not raise UnicodeEncodeError
        self.assertRaises(socket.error, getaddrinfo, host, port)

    def test_addrinfo_cache2 (self):
        # non-ascii hostname with >63 chars
        host = u"ä"*64
        port = 80
        self.assertRaises(LinkCheckerError, getaddrinfo, host, port)
