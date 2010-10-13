# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2009 Bastian Kleineidam
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
Store and retrieve cookies.
"""
from .. import log, LOG_CACHE, cookies
from ..decorators import synchronized
from ..lock import get_lock


_lock = get_lock("cookie")

class CookieJar (object):
    """
    Cookie storage, implementing the default cookie handling policy for
    LinkChecker.
    """

    def __init__ (self):
        self.cache = {}

    @synchronized(_lock)
    def add (self, headers, scheme, host, path):
        """Parse cookie values, add to cache."""
        jar = self.cache.setdefault(host, set())
        for h in headers.getallmatchingheaders("Set-Cookie"):
            # RFC 2109 (Netscape) cookie type
            try:
                jar.add(cookies.NetscapeCookie(h, scheme, host, path))
            except cookies.CookieError:
                log.debug(LOG_CACHE,
               "Invalid cookie header for %s:%s%s: %r", scheme, host, path, h)
        for h in headers.getallmatchingheaders("Set-Cookie2"):
            # RFC 2965 cookie type
            try:
                jar.add(cookies.Rfc2965Cookie(h, scheme, host, path))
            except cookies.CookieError:
                log.debug(LOG_CACHE,
              "Invalid cookie2 header for %s:%s%s: %r", scheme, host, path, h)
        self.cache[host] = jar
        return jar

    @synchronized(_lock)
    def get (self, scheme, host, port, path):
        """Cookie cache getter function."""
        jar = self.cache.setdefault(host, set())
        cookies = [x for x in jar if x.check_expired() and \
                   x.is_valid_for(scheme, host, port, path)]
        log.debug(LOG_CACHE, "Found %d cookies for host %r path %r",
                  len(cookies), host, path)
        return cookies

    @synchronized(_lock)
    def __str__ (self):
        return "<CookieJar with %s>" % self.cache
