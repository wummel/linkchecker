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
        linkcheck.log.debug(linkcheck.LOG_CACHE, "Cookie expires %s",
                            m["expires"])
        # XXX check cookie expiration
    return m.output(header='').strip()


class Cache (object):
    """Store and provide routines for cached data. Currently there are
       caches for cookies, checked urls, FTP connections and robots.txt
       contents.

       All public operations (except __init__()) are thread-safe.
    """

    def __init__ (self):
        """Initialize the default options"""
        # one big lock for all caches and queues
        self.lock = threading.Lock()
        # already checked urls
        self.checked = {}
        # open FTP connections
        # {(host,user,pass) -> [connection, status]}
        self.ftp_connections = {}
        # urls that are being checked
        self.in_progress = {}
        # to-be-checked urls
        self.incoming = []
        # downloaded robots.txt files
        self.robots_txt = {}
        # stored cookies
        self.cookies = {}

    def incoming_is_empty (self):
        self.lock.acquire()
        try:
            return len(self.incoming) <= 0
        finally:
            self.lock.release()

    def incoming_get_url (self):
        """Get first not-in-progress url from the incoming queue and
           return it. If no such url is available return None. The
           url might be already cached."""
        self.lock.acquire()
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
            self.lock.release()

    def incoming_len (self):
        """return number of entries in incoming queue"""
        self.lock.acquire()
        try:
            return len(self.incoming)
        finally:
            self.lock.release()

    def incoming_add (self, url_data):
        """add a new URL to list of URLs to check"""
        self.lock.acquire()
        try:
            linkcheck.log.debug(linkcheck.LOG_CACHE, "Add url %s..", url_data)
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
            linkcheck.log.debug(linkcheck.LOG_CACHE, "..added.")
            return True
        finally:
            self.lock.release()

    def has_incoming (self, key):
        self.lock.acquire()
        try:
            return key in self.incoming
        finally:
            self.lock.release()

    def has_in_progress (self, key):
        self.lock.acquire()
        try:
            return key in self.in_progress
        finally:
            self.lock.release()

    def in_progress_remove (self, url_data):
        """remove url from in-progress cache"""
        self.lock.acquire()
        try:
            key = url_data.cache_url_key
            assert key in self.in_progress
            del self.in_progress[key]
        finally:
            self.lock.release()

    def checked_add (self, url_data):
        """cache checked url data"""
        self.lock.acquire()
        try:
            data = url_data.get_cache_data()
            key = url_data.cache_url_key
            assert key not in self.checked
            assert key in self.in_progress
            # move entry from self.in_progress to self.checked
            del self.in_progress[key]
            self.checked[key] = data
            # also add all aliases to self.checked
            for key in url_data.aliases:
                self.checked[key] = data
        finally:
            self.lock.release()

    def checked_redirect (self, redirect, url_data):
        """Check if redirect is already in cache. Used for URL redirections
           to avoid double checking of already cached URLs.
           If the redirect URL is found in the cache, the result data is
           already copied."""
        self.lock.acquire()
        try:
            if redirect in self.checked:
                url_data.copy_from_cache(self.checked[redirect])
                return True
            return False
        finally:
            self.lock.release()

    def robots_txt_allows_url (self, url_data):
        """ask robots.txt allowance"""
        self.lock.acquire()
        try:
            roboturl = url_data.get_robots_txt_url()
            linkcheck.log.debug(linkcheck.LOG_CACHE,
                       "robots.txt url %r of %r", roboturl, url_data.url)
            if roboturl not in self.robots_txt:
                user, password = url_data.get_user_password()
                rp = linkcheck.robotparser2.RobotFileParser(
                                                user=user, password=password)
                rp.set_url(roboturl)
                rp.read()
                self.robots_txt[roboturl] = rp
            else:
                rp = self.robots_txt[roboturl]
            return rp.can_fetch(linkcheck.configuration.UserAgent,
                                url_data.url)
        finally:
            self.lock.release()

    def get_ftp_connection (self, host, username, password):
        """Get open FTP connection to given host. Return None if no such
           connection is available.
        """
        self.lock.acquire()
        try:
            key = (host, username, password)
            if key in self.ftp_connections:
                conn_and_status = self.ftp_connections[key]
                if conn_and_status[1] == 'busy':
                    # connection is in use
                    return None
                conn_and_status[1] = 'busy'
                return conn_and_status[0]
        finally:
            self.lock.release()

    def add_ftp_connection (self, host, username, password, conn):
        """Store open FTP connection into cache for reuse."""
        self.lock.acquire()
        try:
            key = (host, username, password)
            cached = key in self.ftp_connections
            if not cached:
                self.ftp_connections[key] = [conn, 'busy']
            return cached
        finally:
            self.lock.release()

    def release_ftp_connection (self, host, username, password):
        """Store open FTP connection into cache for reuse."""
        self.lock.acquire()
        try:
            key = (host, username, password)
            self.ftp_connections[key][1] = 'available'
        finally:
            self.lock.release()

    def store_cookies (self, headers, host):
        """Thread-safe cookie cache setter function. Can raise the
           exception Cookie.CookieError.
        """
        self.lock.acquire()
        try:
            output = []
            for h in headers.getallmatchingheaders("Set-Cookie"):
                output.append(h)
                linkcheck.log.debug(linkcheck.LOG_CACHE, "Store Cookie %s", h)
                c = self.cookies.setdefault(host, Cookie.SimpleCookie())
                c.load(h)
            return output
        finally:
            self.lock.release()

    def get_cookies (self, host, path):
        """Thread-safe cookie cache getter function."""
        self.lock.acquire()
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
            self.lock.release()
