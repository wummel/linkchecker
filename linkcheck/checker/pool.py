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

    def __init__ (self):
        # open connections
        # {(type, host, user, pass) -> [connection, status, timeout]}
        self.connections = {}

    def add_connection (self, key, conn, timeout):
        cached = key in self.connections
        if not cached:
            self.connections[key] = [conn, 'available', time.time() + timeout]
        return cached

    def get_connection (self, key):
        if key not in self.connections:
            # not found
            return None
        conn_data = self.connections[key]
        t = time.time()
        if t > conn_data[2]:
            # timed out
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
        if key in self.connections:
            self.connections[key][1] = 'available'
