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

