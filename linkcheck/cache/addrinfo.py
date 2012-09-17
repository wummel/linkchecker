# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2012 Bastian Kleineidam
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
from .. import LinkCheckerError
from ..lock import get_lock
from ..containers import LFUCache
from ..decorators import synchronized

_lock = get_lock("addrinfo")

class AddrInfo(object):

    def __init__(self):
        self.addrinfos = LFUCache(size=100)
        self.misses = self.hits = 0

    def getaddrinfo(self, host, port):
        """Determine address information for given host and port for
        streaming sockets (SOCK_STREAM).
        Already cached information is used."""
        key = u"%s:%s" % (unicode(host), unicode(port))
        if key in self.addrinfos:
            self.hits += 1
            value = self.addrinfos[key]
        else:
            self.misses += 1
            # check if it's an ascii host
            if isinstance(host, unicode):
                try:
                    host = host.encode('ascii')
                except UnicodeEncodeError:
                    pass
            try:
                value = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
            except socket.error:
                value = sys.exc_info()[1]
            except UnicodeError, msg:
                args = dict(host=host, msg=str(msg))
                value = LinkCheckerError(_("could not parse host %(host)r: %(msg)s") % args)
            self.addrinfos[key] = value
        if isinstance(value, Exception):
            raise value
        return value

_addrinfo = AddrInfo()

@synchronized(_lock)
def getaddrinfo(host, port):
    """Determine address information for given host and port for
    streaming sockets (SOCK_STREAM).
    Already cached information is used."""
    return _addrinfo.getaddrinfo(host, port)

@synchronized(_lock)
def getstats():
    """Get cache statistics.
    @return: hits and misses
    @rtype tuple(int, int)
    """
    return _addrinfo.hits, _addrinfo.misses
