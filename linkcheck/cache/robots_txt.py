# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2007 Bastian Kleineidam
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
Cache robots.txt contents.
"""
from linkcheck.decorators import synchronized
import linkcheck.robotparser2
import linkcheck.configuration
import linkcheck.lock
import linkcheck.url


# lock for caching
_lock = linkcheck.lock.get_lock("robots.txt")


class RobotsTxt (object):
    """
    Thread-safe cache of downloaded robots.txt files.
    format: {cache key (string) -> robots.txt content (RobotFileParser)}
    """

    def __init__ (self):
        self.cache = {}

    @synchronized(_lock)
    def allows_url (self, roboturl, url, user, password, callback=None):
        """
        Ask robots.txt allowance.
        """
        if roboturl not in self.cache:
            rp = linkcheck.robotparser2.RobotFileParser(
                                            user=user, password=password)
            rp.set_url(roboturl)
            rp.read()
            if callback is not None:
                parts = linkcheck.url.url_split(rp.url)
                host = "%s:%d" % (parts[1], parts[2])
                useragent = linkcheck.configuration.UserAgent
                wait = rp.get_crawldelay(useragent)
                callback(host, wait)
            self.cache[roboturl] = rp
        else:
            rp = self.cache[roboturl]
        return rp.can_fetch(linkcheck.configuration.UserAgent, url)
