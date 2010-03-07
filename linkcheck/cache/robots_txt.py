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
Cache robots.txt contents.
"""
from .. import robotparser2, configuration, url as urlutil
from ..decorators import synchronized
from ..lock import get_lock


# lock for caching
_lock = get_lock("robots.txt")


class RobotsTxt (object):
    """
    Thread-safe cache of downloaded robots.txt files.
    format: {cache key (string) -> robots.txt content (RobotFileParser)}
    """

    def __init__ (self):
        self.cache = {}

    @synchronized(_lock)
    def allows_url (self, roboturl, url, proxy, user, password, callback=None):
        """
        Ask robots.txt allowance.
        """
        useragent = str(configuration.UserAgent)
        if roboturl not in self.cache:
            rp = robotparser2.RobotFileParser(proxy=proxy, user=user,
                password=password)
            rp.set_url(roboturl)
            rp.read()
            if hasattr(callback, '__call__'):
                parts = urlutil.url_split(rp.url)
                host = "%s:%d" % (parts[1], parts[2])
                wait = rp.get_crawldelay(useragent)
                callback(host, wait)
            self.cache[roboturl] = rp
        else:
            rp = self.cache[roboturl]
        return rp.can_fetch(useragent, url)
