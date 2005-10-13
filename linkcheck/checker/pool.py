# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005  Bastian Kleineidam
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

class ConnectionPool (object):
    """
    Connection pool class, storing a set of connections for URL retrieval.
    """

    def __init__ (self):
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
        self.expiration_counter = 1

    def add_connection (self, key, conn, timeout):
        """
        Add connection to the pool with given identifier key and timeout
        in seconds.
        """
        self.connections[key] = [conn, 'available', time.time() + timeout]

    def get_connection (self, key):
        """
        Get open connection if available, for at most 30 seconds.

        @return: Open connection object or None if no connection is available.
        @rtype None or FTPConnection or HTTP(S)Connection
        """
        if (self.expiration_counter % 100) == 0:
            self.expiration_counter = 1
            self.expire_connections()
        else:
            self.expiration_counter += 1
        if key not in self.connections:
            # not found
            return None
        conn_data = self.connections[key]
        t = time.time()
        if t > conn_data[2]:
            # timed out
            try:
                conn_data[1].close()
            except:
                # ignore close errors
                pass
            del self.connections[key]
            return None
        # wait at most 300*0.1=30 seconds for connection to become available
        for dummy in xrange(300):
            if conn_data[1] != 'busy':
                conn_data[1] = 'busy'
                conn_data[2] = t
                return conn_data[0]
            time.sleep(0.1)
        # connection is in use
        return None

    def release_connection (self, key):
        """
        Mark an open and reusable connection as available.
        """
        if key in self.connections:
            self.connections[key][1] = 'available'

    def expire_connections (self):
        """
        Remove expired connections from this pool.
        """
        t = time.time()
        to_delete = []
        for key, conn_data in self.connections.iteritems():
            if conn_data[1] == 'available' and t > conn_data[2]:
                to_delete.append(key)
        for key in to_delete:
            del self.connections[key]
