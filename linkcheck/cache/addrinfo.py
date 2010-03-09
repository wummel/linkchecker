# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2010 Bastian Kleineidam
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
Cache for DNS lookups.
"""
import socket
import sys
from ..lock import get_lock
from ..containers import LFUCache
from ..decorators import synchronized

_lock = get_lock("addrinfo")
addrinfos = LFUCache(size=10000)

@synchronized(_lock)
def getaddrinfo (host, port):
    key = u"%s:%s" % (unicode(host), unicode(port))
    if key in addrinfos:
        value = addrinfos[key]
    else:
        try:
            value = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        except socket.error:
            value = sys.exc_info()[1]
        addrinfos[key] = value
    if isinstance(value, Exception):
        raise value
    return value

