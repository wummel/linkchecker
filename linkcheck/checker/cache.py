# -*- coding: iso-8859-1 -*-
"""store cached data during checking"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import Cookie
try:
    import threading
except ImportError:
    import dummy_threading as threading

import linkcheck
import linkcheck.log
import linkcheck.containers
import linkcheck.configuration
import linkcheck.threader

from linkcheck.i18n import _

MAX_ROBOTS_TXT_CACHE = 5000
MAX_COOKIES_CACHE = 500


def _check_morsel (m, host, path):
    """check given cookie morsel against the desired host and path"""
    # check domain (if its stored)
    if m["domain"] and not host.endswith(m["domain"]):
        return None
    # check path (if its stored)
    if m["path"] and not path.startswith(m["path"]):
        return None
    # check expiry date (if its stored)
    if m["expires"]:
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Cookie expires %s",
                            m["expires"])
        # XXX
    return m.output(header='').strip()


class Cache (object):
    """Store and provide routines for cached data. Currently there are
       caches for cookies, check urls and robots.txt contents.

       All public operations (except __init__()) are thread-safe.
    """

    def __init__ (self):
        """Initialize the default options"""
        # one big lock for all caches
        self.lock = threading.Lock()
        # caches
        self.url_data_cache = {}
        self.robots_txt_cache = \
                               linkcheck.containers.LRU(MAX_ROBOTS_TXT_CACHE)
        self.cookies = linkcheck.containers.LRU(MAX_COOKIES_CACHE)

    def check_cache (self, url_data):
        """if url_data is already cached, fill it with the cached data
           and return True; else return False"""
        self.lock.acquire()
        try:
            return self._check_cache(url_data)
        finally:
            self.lock.release()

    def _check_cache (self, url_data):
        """internal thread-unsafe check cache method"""
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking cache")
        for key in url_data.get_cache_keys():
            if key in self.url_data_cache:
                url_data.copy_from_cache(self.url_data_cache[key])
                return True
        return False

    def url_data_cache_add (self, url_data):
        """put url data into cache"""
        self.lock.acquire()
        try:
            if url_data.get_cache_key() in self.url_data_cache:
                # another thread was faster and cached this url already
                return
            data = url_data.get_cache_data()
            for key in url_data.get_cache_keys():
                self.url_data_cache[key] = data
        finally:
            self.lock.release()

    def url_is_cached (self, key):
        """return True if given key is in url_data cache"""
        self.lock.acquire()
        try:
            return key in self.url_data_cache
        finally:
            self.lock.release()

    def robots_txt_allows_url (self, url_data):
        """ask robots.txt allowance"""
        self.lock.acquire()
        try:
            roboturl = url_data.get_robots_txt_url()
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                       "robots.txt url %r of %r", roboturl, url_data.url)
            if roboturl not in self.robots_txt_cache:
                rp = linkcheck.robotparser2.RobotFileParser()
                rp.set_url(roboturl)
                rp.read()
                self.robots_txt_cache[roboturl] = rp
            else:
                rp = self.robots_txt_cache[roboturl]
            return rp.can_fetch(linkcheck.configuration.UserAgent,
                                url_data.url)
        finally:
            self.lock.release()

    def store_cookies (self, headers, host):
        """thread-safe cookie cache setter function"""
        self.lock.acquire()
        try:
            output = []
            for h in headers.getallmatchingheaders("Set-Cookie"):
                output.append(h)
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Store Cookie %s", h)
                c = self.cookies.setdefault(host, Cookie.SimpleCookie())
                c.load(h)
            return output
        finally:
            self.lock.release()

    def get_cookies (self, host, path):
        """thread-safe cookie cache getter function"""
        self.lock.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "Get Cookie %s (%s)", host, path)
            if not self.cookies.has_key(host):
                return []
            cookievals = []
            for m in self.cookies[host].values():
                val = _check_morsel(m, host, path)
                if val:
                    cookievals.append(val)
            return cookievals
        finally:
            self.lock.release()
