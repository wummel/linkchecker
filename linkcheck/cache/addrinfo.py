# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
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
Cache for DNS lookups.
"""
import socket
import sys
import linkcheck.lock
from linkcheck.decorators import synchronized

_lock = linkcheck.lock.get_lock("addrinfo")
addrinfos = {}

@synchronized(_lock)
def getaddrinfo (host, port):
    key = str(host) + u":" + str(port)
    if key not in addrinfos:
        try:
            addrinfos[key] = \
                socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        except socket.error:
            addrinfos[key] = sys.exc_info()[1]
    value = addrinfos[key]
    if isinstance(value, Exception):
        raise value
    return value

