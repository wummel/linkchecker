# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
Store cached data during checking.
"""

import Cookie
import collections

import linkcheck
import linkcheck.log
import linkcheck.lock
import linkcheck.containers
import linkcheck.configuration
import linkcheck.threader
import linkcheck.checker.pool


def _check_morsel (m, host, path):
    """
    Check given cookie morsel against the desired host and path.
    """
    # check domain (if its stored)
    if m["domain"] and not host.endswith(m["domain"]):
        return None
    # check path (if its stored)
    if m["path"] and not path.startswith(m["path"]):
        return None
    # check expiry date (if its stored)
    if m["expires"]:
        linkcheck.log.debug(linkcheck.LOG_CACHE, "Cookie expires %s",
                            m["expires"])
        # XXX check cookie expiration
    return m.output(header='').strip()


class Cache (linkcheck.lock.AssertLock):
    """
    Store and provide routines for cached data. Currently there are
    caches for cookies, checked URLs, FTP connections and robots.txt
    contents.

    All public operations (except __init__()) are thread-safe.
    """

    def __init__ (self):
        """
        Initialize the default options.
        """
        super(Cache, self).__init__()
        # already checked URLs
        self.checked = {}
        # URLs that are being checked
        self.in_progress = {}
        # to-be-checked URLs
        self.incoming = collections.deque()
        # downloaded robots.txt files
        self.robots_txt = {}
        # stored cookies
        self.cookies = {}
        # pooled connections
        self.pool = linkcheck.checker.pool.ConnectionPool()

    def incoming_is_empty (self):
        """
        Check if incoming queue is empty.
        """
        self.acquire()
        try:
            return len(self.incoming) <= 0
        finally:
            self.release()

    def incoming_get_url (self):
        """
        Get first not-in-progress url from the incoming queue and
        return it. If no such url is available return None. The
        url might be already cached.
        """
        self.acquire()
        try:
            for i, url_data in enumerate(self.incoming):
                key = url_data.cache_url_key
                if key in self.checked:
                    del self.incoming[i]
                    # url is cached and can be logged
                    url_data.copy_from_cache(self.checked[key])
                    return url_data
                elif key not in self.in_progress:
                    del self.incoming[i]
                    self.in_progress[key] = url_data
                    return url_data
            return None
        finally:
            self.release()

    def incoming_len (self):
        """
        Return number of entries in incoming queue.
        """
        self.acquire()
        try:
            return len(self.incoming)
        finally:
            self.release()

    def incoming_add (self, url_data):
        """
        Add a new URL to list of URLs to check.
        """
        self.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CACHE,
                                "Add url %s...", repr(url_data))
            # check syntax
            if not url_data.check_syntax():
                # wrong syntax, do not check any further
                return False
            # check the cache
            key = url_data.cache_url_key
            if key in self.checked:
                # url is cached and can be logged
                url_data.copy_from_cache(self.checked[key])
                return False
            # url is not cached, so add to incoming queue
            self.incoming.append(url_data)
            linkcheck.log.debug(linkcheck.LOG_CACHE, "...added.")
            return True
        finally:
            self.release()

    def has_incoming (self, key):
        """
        Check if incoming queue has an entry with the given key.

        @param key: Usually obtained from url_data.cache_url_key
        @type key: String
        """
        self.acquire()
        try:
            return key in self.incoming
        finally:
            self.release()

    def has_in_progress (self, key):
        """
        Check if in-progress queue has an entry with the given key.

        @param key: Usually obtained from url_data.cache_url_key
        @type key: String
        """
        self.acquire()
        try:
            return key in self.in_progress
        finally:
            self.release()

    def in_progress_remove (self, url_data, ignore_missing=False):
        """
        Remove url from in-progress cache. If url is not cached and
        ignore_missing evaluates True, raise AssertionError.
        """
        self.acquire()
        try:
            key = url_data.cache_url_key
            if key in self.in_progress:
                del self.in_progress[key]
            else:
                assert ignore_missing, repr(key)
        finally:
            self.release()

    def checked_add (self, url_data):
        """
        Cache checked url data.
        """
        self.acquire()
        try:
            data = url_data.get_cache_data()
            key = url_data.cache_url_key
            linkcheck.log.debug(linkcheck.LOG_CACHE, "Cache key %r...", key)
            assert key not in self.checked, \
                   key + u", " + unicode(self.checked[key])
            assert key in self.in_progress, key
            # move entry from self.in_progress to self.checked
            del self.in_progress[key]
            self.checked[key] = data
        finally:
            self.release()

    def checked_redirect (self, redirect, url_data):
        """
        Check if redirect is already in cache. Used for URL redirections
        to avoid double checking of already cached URLs.
        If the redirect URL is found in the cache, the result data is
        already copied.
        """
        self.acquire()
        try:
            if redirect in self.checked:
                url_data.copy_from_cache(self.checked[redirect])
                return True
            return False
        finally:
            self.release()

    def robots_txt_allows_url (self, roboturl, url, user, password):
        """
        Ask robots.txt allowance.
        """
        self.acquire()
        try:
            if roboturl not in self.robots_txt:
                rp = linkcheck.robotparser2.RobotFileParser(
                                                user=user, password=password)
                rp.set_url(roboturl)
                rp.read()
                self.robots_txt[roboturl] = rp
            else:
                rp = self.robots_txt[roboturl]
            return rp.can_fetch(linkcheck.configuration.UserAgent, url)
        finally:
            self.release()

    def get_connection (self, key):
        """
        Get open connection to given host. Return None if no such
        connection is available (or the old one timed out).
        """
        self.acquire()
        try:
            return self.pool.get_connection(key)
        finally:
            self.release()

    def add_connection (self, key, connection, timeout):
        """
        Store open connection into pool for reuse.
        """
        self.acquire()
        try:
            self.pool.add_connection(key, connection, timeout)
        finally:
            self.release()

    def release_connection (self, key):
        """
        Remove connection from pool.
        """
        self.acquire()
        try:
            self.pool.release_connection(key)
        finally:
            self.release()

    def store_cookies (self, headers, host):
        """
        Thread-safe cookie cache setter function. Can raise the
        exception Cookie.CookieError.
        """
        self.acquire()
        try:
            output = []
            for h in headers.getallmatchingheaders("Set-Cookie"):
                output.append(h)
                linkcheck.log.debug(linkcheck.LOG_CACHE, "Store Cookie %s", h)
                c = self.cookies.setdefault(host, Cookie.SimpleCookie())
                c.load(h)
            return output
        finally:
            self.release()

    def get_cookies (self, host, path):
        """
        Thread-safe cookie cache getter function.
        """
        self.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CACHE,
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
            self.release()
