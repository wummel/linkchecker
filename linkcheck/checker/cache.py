# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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

import collections
import linkcheck
import linkcheck.log
import linkcheck.lock
import linkcheck.containers
import linkcheck.configuration
import linkcheck.cookies
import linkcheck.threader
import linkcheck.checker.pool


class Cache (object):
    """
    Store and provide routines for cached data. Currently there are
    caches for cookies, checked URLs, FTP connections and robots.txt
    contents.
    """

    def __init__ (self):
        """
        Initialize the default options.
        """
        super(Cache, self).__init__()
        # already checked URLs
        # format: {cache key (string) -> cache data (dict)}
        self.checked = {}
        # URLs that are being checked
        # format: {cache key (string) -> urldata (UrlData)}
        self.in_progress = {}
        # to-be-checked URLs
        # format: [urldata (UrlData)]
        self.incoming = collections.deque()
        # downloaded robots.txt files
	# format: {cache key (string) -> robots.txt content (RobotFileParser)}
        self.robots_txt = {}
        # stored cookies
	# format: {cache key (string) -> cookie jar (linkcheck.cookielib.CookieJar)}
        self.cookies = {}
        # pooled connections
        self.pool = linkcheck.checker.pool.ConnectionPool()

    def incoming_is_empty (self):
        """
        Check if incoming queue is empty.
        """
        return len(self.incoming) <= 0

    def incoming_get_url (self):
        """
        Get first not-in-progress url from the incoming queue and
        return it. If no such url is available return None. The
        url might be already cached.
        """
        res = None
        to_delete = None
        for i, url_data in enumerate(self.incoming):
            key = url_data.cache_url_key
            if key in self.checked:
                to_delete = i
                # url is cached and can be logged
                url_data.copy_from_cache(self.checked[key])
                res = url_data
                break
            elif key not in self.in_progress:
                to_delete = i
                self.in_progress[key] = url_data
                res = url_data
                break
        if to_delete is not None:
            del self.incoming[i]
        return res

    def incoming_len (self):
        """
        Return number of entries in incoming queue.
        """
        return len(self.incoming)

    def incoming_add (self, url_data):
        """
        Add a new URL to list of URLs to check.
        """
        assert linkcheck.log.debug(linkcheck.LOG_CACHE,
                                   "Add url %r ...", url_data)
        if url_data.has_result:
            # do not check any further
            assert linkcheck.log.debug(linkcheck.LOG_CACHE,
                                       "... no, has result")
            return False
        # check the cache
        key = url_data.cache_url_key
        if key in self.checked:
            # url is cached and can be logged
            url_data.copy_from_cache(self.checked[key])
            assert linkcheck.log.debug(linkcheck.LOG_CACHE, "... no, cached")
            return False
        # url is not cached, so add to incoming queue
        self.incoming.append(url_data)
        assert linkcheck.log.debug(linkcheck.LOG_CACHE, "... yes, added.")
        return True

    def has_in_progress (self, key):
        """
        Check if in-progress queue has an entry with the given key.

        @param key: Usually obtained from url_data.cache_url_key
        @type key: String
        """
        return key in self.in_progress

    def in_progress_remove (self, url_data, ignore_missing=False):
        """
        Remove url from in-progress cache. If url is not cached and
        ignore_missing evaluates True, raise AssertionError.
        """
        key = url_data.cache_url_key
        if key in self.in_progress:
            del self.in_progress[key]
        else:
            assert ignore_missing, repr(key)

    def checked_add (self, url_data):
        """
        Cache checked url data.
        """
        data = url_data.get_cache_data()
        key = url_data.cache_url_key
        assert linkcheck.log.debug(linkcheck.LOG_CACHE, "Caching %r", key)
        assert key not in self.checked, \
               key + u", " + unicode(self.checked[key])
        assert key in self.in_progress, key
        # move entry from self.in_progress to self.checked
        del self.in_progress[key]
        self.checked[key] = data
        # check for aliases (eg. through HTTP redirections)
        if hasattr(url_data, "aliases"):
            data = url_data.get_alias_cache_data()
            for key in url_data.aliases:
                if key not in self.checked and key not in self.in_progress:
                    assert linkcheck.log.debug(linkcheck.LOG_CACHE,
                                        "Caching alias %r", key)
                    self.checked[key] = data

    def checked_redirect (self, redirect, url_data):
        """
        Check if redirect is already in cache. Used for URL redirections
        to avoid double checking of already cached URLs.
        If the redirect URL is found in the cache, the result data is
        already copied.
        """
        if redirect in self.checked:
            url_data.copy_from_cache(self.checked[redirect])
            return True
        return False

    def robots_txt_allows_url (self, roboturl, url, user, password):
        """
        Ask robots.txt allowance.
        """
        if roboturl not in self.robots_txt:
            rp = linkcheck.robotparser2.RobotFileParser(
                                            user=user, password=password)
            rp.set_url(roboturl)
            rp.read()
            self.robots_txt[roboturl] = rp
        else:
            rp = self.robots_txt[roboturl]
        return rp.can_fetch(linkcheck.configuration.UserAgent, url)

    def get_connection (self, key):
        """
        Get open connection to given host. Return None if no such
        connection is available (or the old one timed out).
        """
        return self.pool.get_connection(key)

    def add_connection (self, key, connection, timeout):
        """
        Store open connection into pool for reuse.
        """
        self.pool.add_connection(key, connection, timeout)

    def release_connection (self, key):
        """
        Remove connection from pool.
        """
        self.pool.release_connection(key)

    def store_cookies (self, headers, scheme, host, path):
        """
        Thread-safe cookie cache setter function. Can raise the
        exception Cookie.CookieError.
        """
        jar = self.cookies.setdefault(host, linkcheck.cookies.CookieJar())
        return jar.add_cookies(headers, scheme, host, path)

    def get_cookies (self, scheme, host, port, path):
        """
        Thread-safe cookie cache getter function.
        """
        assert linkcheck.log.debug(linkcheck.LOG_CACHE,
                            "Get cookies for host %r path %r", host, path)
        jar = self.cookies.setdefault(host, linkcheck.cookies.CookieJar())
        jar.remove_expired()
        return [x for x in jar if x.is_valid_for(scheme, host, port, path)]

