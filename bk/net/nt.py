# -*- coding: iso-8859-1 -*-
"""network utilities for windows platforms"""
# Copyright (C) 2004  Bastian Kleineidam
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

import sets
import bk.winreg


def get_localaddrs ():
    """all active interfaces' ip addresses"""
    addrs = sets.Set()
    try: # search interfaces
        key = bk.winreg.key_handle(bk.winreg.HKEY_LOCAL_MACHINE,
           r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces")
        for subkey in key.subkeys():
            if subkey.get('EnableDHCP'):
                ip = subkey.get('DhcpIPAddress', '')
            else:
                ip = subkey.get('IPAddress', '')
            if not (isinstance(ip, basestring) and ip):
                continue
            addrs.add(str(ip).lower())
    except EnvironmentError:
        pass
    return addrs


def resolver_config (config):
    """get DNS config from Windows registry settings"""
    try:
        key = bk.winreg.key_handle(bk.winreg.HKEY_LOCAL_MACHINE,
               r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
    except EnvironmentError:
        try: # for Windows ME
            key = bk.winreg.key_handle(bk.winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Services\VxD\MSTCP")
        except EnvironmentError:
            key = None
    if key:
        if key.get('EnableDHCP'):
            servers = bk.winreg.stringdisplay(key.get("DhcpNameServer", ""))
            domains = key.get("DhcpDomain", "").split()
        else:
            servers = bk.winreg.stringdisplay(key.get("NameServer", ""))
            domains = key.get("SearchList", "").split()
        config.nameservers.extend([ str(s).lower() for s in servers if s ])
        config.search_domains.extend([ str(d).lower() for d in domains if d ])
    try: # search adapters
        key = bk.winreg.key_handle(bk.winreg.HKEY_LOCAL_MACHINE,
  r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\DNSRegisteredAdapters")
    except EnvironmentError:
        key = None
    if key:
        for subkey in key.subkeys():
            values = subkey.get("DNSServerAddresses", "")
            servers = bk.winreg.binipdisplay(values)
            config.nameservers.extend([ str(s).lower() for s in servers if s ])
    try: # search interfaces
        key = bk.winreg.key_handle(bk.winreg.HKEY_LOCAL_MACHINE,
           r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces")
    except EnvironmentError:
        key = None
    if key:
        for subkey in key.subkeys():
            if subkey.get('EnableDHCP'):
                servers = bk.winreg.stringdisplay(subkey.get('DhcpNameServer', ''))
                domains = subkey.get("DhcpDomain", "").split()
            else:
                servers = bk.winreg.stringdisplay(subkey.get('NameServer', ''))
                domains = subkey.get("SearchList", "").split()
            config.nameservers.extend([ str(s).lower() for s in servers if s ])
            config.search_domains.extend([ str(d).lower() for d in domains if d ])

