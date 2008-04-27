# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2008 Bastian Kleineidam
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
Store and retrieve cookies.
"""
from linkcheck.decorators import synchronized
from .. import log, LOG_CACHE
import linkcheck.lock
import linkcheck.cookies


_lock = linkcheck.lock.get_lock("cookie")

class CookieJar (object):
    """
    Cookie storage, implementing the default cookie handling policy for
    LinkChecker.
    """

    def __init__ (self):
        self.cache = {}

    @synchronized(_lock)
    def add (self, headers, scheme, host, path):
        """
        Parse cookie values, add to cache.
        """
        jar = set()
        for h in headers.getallmatchingheaders("Set-Cookie"):
            # RFC 2109 (Netscape) cookie type
            try:
                c = linkcheck.cookies.NetscapeCookie(h, scheme, host, path)
                jar.add(c)
            except linkcheck.cookies.CookieError:
                log.debug(LOG_CACHE,
               "Invalid cookie header for %s:%s%s: %r", scheme, host, path, h)
        for h in headers.getallmatchingheaders("Set-Cookie2"):
            # RFC 2965 cookie type
            try:
                c = linkcheck.cookies.Rfc2965Cookie(h, scheme, host, path)
                jar.add(c)
            except linkcheck.cookies.CookieError:
                log.debug(LOG_CACHE,
              "Invalid cookie2 header for %s:%s%s: %r", scheme, host, path, h)
        self.cache[host] = jar
        return jar

    @synchronized(_lock)
    def get (self, scheme, host, port, path):
        """
        Cookie cache getter function.
        """
        log.debug(LOG_CACHE, "Get cookies for host %r path %r", host, path)
        jar = self.cache.setdefault(host, set())
        return [x for x in jar if x.check_expired() and \
                x.is_valid_for(scheme, host, port, path)]

    @synchronized(_lock)
    def __str__ (self):
        return "<CookieJar with %s>" % self.cache
