# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
from .. import robotparser2, configuration
from ..containers import LFUCache
from ..decorators import synchronized
from ..lock import get_lock


# lock objects
cache_lock = get_lock("robots.txt_cache_lock")
robot_lock = get_lock("robots.txt_robot_lock")


class RobotsTxt (object):
    """
    Thread-safe cache of downloaded robots.txt files.
    format: {cache key (string) -> robots.txt content (RobotFileParser)}
    """
    useragent = str(configuration.UserAgent)

    def __init__ (self):
        """Initialize per-URL robots.txt cache."""
        # mapping {URL -> parsed robots.txt}
        self.cache = LFUCache(size=100)
        self.hits = self.misses = 0
        self.roboturl_locks = {}

    def allows_url (self, roboturl, url, proxy, user, password):
        """Ask robots.txt allowance."""
        with self.get_lock(roboturl):
            return self._allows_url(roboturl, url, proxy, user, password)

    def _allows_url (self, roboturl, url, proxy, user, password):
        """Ask robots.txt allowance. Assumes only single thread per robots.txt
        URL calls this function."""
        with cache_lock:
            if roboturl in self.cache:
                self.hits += 1
                rp = self.cache[roboturl]
                return rp.can_fetch(self.useragent, url)
            self.misses += 1
        rp = robotparser2.RobotFileParser(proxy=proxy, user=user,
            password=password)
        rp.set_url(roboturl)
        rp.read()
        with cache_lock:
            self.cache[roboturl] = rp
        return rp.can_fetch(self.useragent, url)

    @synchronized(robot_lock)
    def get_lock(self, roboturl):
        """Return lock for robots.txt url."""
        return self.roboturl_locks.setdefault(roboturl, get_lock(roboturl))
