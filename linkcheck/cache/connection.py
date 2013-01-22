# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2012 Bastian Kleineidam
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
Store and retrieve open connections.
"""

import time
from .. import log, LOG_CACHE
from ..decorators import synchronized
from ..lock import get_lock, get_semaphore
from ..containers import enum

_lock = get_lock("connection")
_wait_lock = get_lock("connwait")

ConnectionTypes = ("ftp", "http", "https")
ConnectionState = enum("available", "busy")

DefaultLimits = dict(
    http=10,
    https=10,
    ftp=2,
)

def get_connection_id(connection):
    """Return unique id for connection object."""
    return id(connection)


def is_expired(curtime, conn_data):
    """Test if connection is expired."""
    return (curtime+5.0) >= conn_data[2]


class ConnectionPool (object):
    """Thread-safe cache, storing a set of connections for URL retrieval."""

    def __init__ (self, wait=0, limits=None):
        """
        Initialize an empty connection dictionary which will have the form:
        {(type, host, port) -> (lock, {id -> [connection, state, expiration time]})}

        Connection can be any open connection object (HTTP, FTP, ...).
        State is of type ConnectionState (either 'available' or 'busy').
        Expiration time is the point of time in seconds when this
        connection will be timed out.

        The type is the connection type and an either 'ftp' or 'http'.
        The host is the hostname as string, port the port number as an integer.

        For each type, the maximum number of connection can be defined. The default
        is 4 for http/1.0, 2 for http/1.1 and 2 for ftp.
        """
        # open connections
        self.connections = {}
        # {host -> due time}
        self.times = {}
        # {host -> wait}
        self.host_waits = {}
        if wait < 0:
            raise ValueError("negative wait value %d" % wait)
        self.wait = wait
        if limits is None:
            self.limits = DefaultLimits
        else:
            self.limits = {}
            for type in ConnectionTypes:
                self.limits[type] = limits.get(type, DefaultLimits[type])

    @synchronized(_wait_lock)
    def host_wait (self, host, wait):
        """Set a host specific time to wait between requests."""
        if wait < 0:
            raise ValueError("negative wait value %d" % wait)
        self.host_waits[host] = wait

    @synchronized(_wait_lock)
    def wait_for_host (self, host):
        """Honor wait time for given host."""
        t = time.time()
        if host in self.times:
            due_time = self.times[host]
            if due_time > t:
                wait = due_time - t
                log.debug(LOG_CACHE,
                  "waiting for %.01f seconds on connection to %s", wait, host)
                time.sleep(wait)
                t = time.time()
        self.times[host] = t + self.host_waits.get(host, self.wait)

    def _add (self, type, host, port, create_connection):
        """Add connection to the pool with given parameters.

        @param type: the connection scheme (eg. http)
        @ptype type: string
        @param host: the hostname
        @ptype host: string
        @param port: the port number
        @ptype port: int
        @param create_connection: function to create a new connection object
        @ptype create_connection: callable
        @return: newly created connection
        @rtype: HTTP(S)Connection or FTPConnection
        """
        self.wait_for_host(host)
        connection = create_connection(type, host, port)
        cid = get_connection_id(connection)
        expiration = None
        conn_data = [connection, 'busy', expiration]
        key = (type, host, port)
        if key in self.connections:
            lock, entries = self.connections[key]
            entries[cid] = conn_data
        else:
            lock = get_semaphore("%s:%d" % (host, port), self.limits[type])
            lock.acquire()
            log.debug(LOG_CACHE, "Acquired lock for %s://%s:%d" % key)
            entries = {cid: conn_data}
            self.connections[key] = (lock, entries)
        return connection

    @synchronized(_lock)
    def get (self, type, host, port, create_connection):
        """Get open connection if available or create a new one.

        @param type: connection type
        @ptype type: ConnectionType
        @param host: hostname
        @ptype host: string
        @param port: port number
        @ptype port: int
        @return: Open connection object or None if none is available.
        @rtype None or FTPConnection or HTTP(S)Connection
        """
        assert type in ConnectionTypes, 'invalid type %r' % type
        # 65536 == 2**16
        assert 0 < port < 65536, 'invalid port number %r' % port
        key = (type, host, port)
        if key not in self.connections:
            return self._add(type, host, port, create_connection)
        lock, entries = self.connections[key]
        if not lock.acquire(False):
            log.debug(LOG_CACHE, "wait for %s connection to %s:%d",
                      type, host, port)
            return lock
        log.debug(LOG_CACHE, "Acquired lock for %s://%s:%d" % key)
        # either a connection is available or a new one can be created
        t = time.time()
        delete_entries = []
        try:
            for id, conn_data in entries.items():
                if conn_data[1] == ConnectionState.available:
                    if is_expired(t, conn_data):
                        delete_entries.append(id)
                    else:
                        conn_data[1] = ConnectionState.busy
                        log.debug(LOG_CACHE,
                          "reusing connection %s timing out in %.01f seconds",
                           key, (conn_data[2] - t))
                        return conn_data[0]
        finally:
            for id in delete_entries:
                del entries[id]
        # make a new connection
        return self._add(type, host, port, create_connection)

    @synchronized(_lock)
    def release (self, type, host, port, connection, expiration=None):
        """Release a used connection."""
        key = (type, host, port)
        if key in self.connections:
            lock, entries = self.connections[key]
            id = get_connection_id(connection)
            if id in entries:
                log.debug(LOG_CACHE, "Release lock for %s://%s:%d and expiration %s", type, host, port, expiration)
                # if the connection is reusable, set it to available, else delete it
                if expiration is None:
                    del entries[id]
                else:
                    entries[id][1] = ConnectionState.available
                    entries[id][2] = expiration
                lock.release()
            else:
                log.warn(LOG_CACHE, "Release unknown connection %s://%s:%d from entries %s", type, host, port, entries.keys())
        else:
            log.warn(LOG_CACHE, "Release unknown connection %s://%s:%d", type, host, port)

    @synchronized(_lock)
    def remove_expired (self):
        """Remove expired or soon to be expired connections from this pool."""
        t = time.time()
        for lock, entries in self.connections.values():
            delete_entries = []
            for id, conn_data in entries.items():
                if conn_data[1] == 'available' and (t+5.0) >= conn_data[2]:
                    try_close(conn_data[0])
                    delete_entries.add(id)
            for id in delete_entries:
                del entries[id]
                lock.release()
                log.debug(LOG_CACHE, "released lock for id %s", id)

    @synchronized(_lock)
    def clear (self):
        """Remove all connections from this cache, even if busy."""
        for lock, entries in self.connections.values():
            for conn_data in entries.values():
                try_close(conn_data[0])
        self.connections.clear()


def try_close (connection):
    """Close and remove a connection (not thread-safe, internal use only)."""
    try:
        connection.close()
    except Exception:
        # ignore close errors
        pass
