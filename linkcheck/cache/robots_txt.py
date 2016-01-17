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
from .. import robotparser2
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

    def __init__ (self, useragent):
        """Initialize per-URL robots.txt cache."""
        # mapping {URL -> parsed robots.txt}
        self.cache = LFUCache(size=100)
        self.hits = self.misses = 0
        self.roboturl_locks = {}
        self.useragent = useragent

    def allows_url (self, url_data):
        """Ask robots.txt allowance."""
        roboturl = url_data.get_robots_txt_url()
        with self.get_lock(roboturl):
            return self._allows_url(url_data, roboturl)

    def _allows_url (self, url_data, roboturl):
        """Ask robots.txt allowance. Assumes only single thread per robots.txt
        URL calls this function."""
        with cache_lock:
            if roboturl in self.cache:
                self.hits += 1
                rp = self.cache[roboturl]
                return rp.can_fetch(self.useragent, url_data.url)
            self.misses += 1
        kwargs = dict(auth=url_data.auth, session=url_data.session)
        if hasattr(url_data, "proxy") and hasattr(url_data, "proxy_type"):
            kwargs["proxies"] = {url_data.proxytype: url_data.proxy}
        rp = robotparser2.RobotFileParser(**kwargs)
        rp.set_url(roboturl)
        rp.read()
        with cache_lock:
            self.cache[roboturl] = rp
        self.add_sitemap_urls(rp, url_data, roboturl)
        return rp.can_fetch(self.useragent, url_data.url)

    def add_sitemap_urls(self, rp, url_data, roboturl):
        """Add sitemap URLs to queue."""
        if not rp.sitemap_urls or not url_data.allows_simple_recursion():
            return
        for sitemap_url, line in rp.sitemap_urls:
            url_data.add_url(sitemap_url, line=line)

    @synchronized(robot_lock)
    def get_lock(self, roboturl):
        """Return lock for robots.txt url."""
        return self.roboturl_locks.setdefault(roboturl, get_lock(roboturl))
