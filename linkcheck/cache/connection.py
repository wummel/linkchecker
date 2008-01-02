# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2008 Bastian Kleineidam
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
Store and retrieve open connections.
"""

import time
import linkcheck.lock
import linkcheck.log
from linkcheck.decorators import synchronized

_lock = linkcheck.lock.get_lock("connection")
_wait_lock = linkcheck.lock.get_lock("connwait")

class ConnectionPool (object):
    """Thread-safe cache, storing a set of connections for URL retrieval."""

    def __init__ (self, wait=0):
        """
        Initialize an empty connection dictionary which will have entries
        of the form::
        key -> [connection, status, expiration time]

        Connection can be any open connection object (HTTP, FTP, ...).
        Status is either 'available' or 'busy'.
        Expiration time is the point of time in seconds when this
        connection will be timed out.

        The identifier key is usually a tuple (type, host, user, pass),
        but it can be any immutable Python object.
        """
        # open connections
        # {(type, host, user, pass) -> [connection, status, expiration time]}
        self.connections = {}
        # {host -> due time}
        self.times = {}
        # {host -> wait}
        self.host_waits = {}
        if wait < 0:
            raise ValueError("negative wait value %d" % wait)
        self.wait = wait

    @synchronized(_lock)
    def host_wait (self, host, wait):
        """Set a host specific time to wait between requests."""
        if wait < 0:
            raise ValueError("negative wait value %d" % wait)
        self.host_waits[host] = wait

    @synchronized(_lock)
    def add (self, key, conn, timeout):
        """Add connection to the pool with given identifier key and timeout
        in seconds."""
        self.connections[key] = [conn, 'available', time.time() + timeout]

    @synchronized(_wait_lock)
    def wait_for_host (self, host):
        t = time.time()
        if host in self.times:
            due_time = self.times[host]
            if due_time > t:
                wait = due_time - t
                assert None == linkcheck.log.debug(linkcheck.LOG_CACHE,
                  "waiting for %.01f seconds on connection to %s", wait, host)
                time.sleep(wait)
                t = time.time()
        self.times[host] = t + self.host_waits.get(host, self.wait)

    @synchronized(_lock)
    def get (self, key):
        """
        Get open connection if available.

        @param key - connection key to look for
        @ptype key - tuple (type, host, user, pass)
        @return: Open connection object or None if none is available.
        @rtype None or FTPConnection or HTTP(S)Connection
        """
        host = key[1]
        if key not in self.connections:
            # not found
            return None
        conn_data = self.connections[key]
        t = time.time()
        if t > conn_data[2]:
            # timed out
            self._remove_connection(key)
            return None
        if conn_data[1] == 'busy':
            # connection is in use
            return None
        # mark busy and return
        conn_data[1] = 'busy'
        conn_data[2] = t
        return conn_data[0]

    @synchronized(_lock)
    def release (self, key):
        """Mark an open and reusable connection as available."""
        if key in self.connections:
            self.connections[key][1] = 'available'

    @synchronized(_lock)
    def remove_expired (self):
        """Remove expired connections from this pool."""
        t = time.time()
        to_delete = []
        for key, conn_data in self.connections.iteritems():
            if conn_data[1] == 'available' and t > conn_data[2]:
                to_delete.append(key)
        for key in to_delete:
            self._remove_connection(key)

    def _remove_connection (self, key):
        """Close and remove a connection (not thread-safe, internal use
        only)."""
        conn_data = self.connections[key]
        del self.connections[key]
        try:
            conn_data[1].close()
        except:
            # ignore close errors
            pass

    @synchronized(_lock)
    def clear (self):
        """Remove all connections from this cache, even if busy."""
        keys = self.connections.keys()
        for key in keys:
            self._remove_connection(key)
