# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2014 Bastian Kleineidam
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
Test network functions.
"""

import unittest
from tests import need_posix, need_network, need_linux
import linkcheck.network
from linkcheck.network import iputil


class TestNetwork (unittest.TestCase):
    """Test network functions."""

    @need_posix
    def test_ifreq_size (self):
        self.assertTrue(linkcheck.network.ifreq_size() > 0)

    @need_posix
    def test_interfaces (self):
        ifc = linkcheck.network.IfConfig()
        ifc.getInterfaceList()

    @need_network
    @need_linux
    def test_iputils (self):
        # note: need a hostname whose reverse lookup of the IP is the same host
        host = "dinsdale.python.org"
        ips = iputil.resolve_host(host)
        self.assertTrue(len(ips) > 0)
        for ip in ips:
            if iputil.is_valid_ipv4(ip):
                obfuscated = iputil.obfuscate_ip(ip)
                self.assertTrue(iputil.is_obfuscated_ip(obfuscated))
                hosts = iputil.lookup_ips([obfuscated])
                self.assertTrue(host in hosts)
