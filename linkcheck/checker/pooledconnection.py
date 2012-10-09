# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012 Bastian Kleineidam
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
Mixin class for URLs that pool connections.
"""


class PooledConnection (object):
    """Support for connection pooling."""

    def get_pooled_connection(self, scheme, host, port, create_connection):
        """Get a connection from the connection pool."""
        get_connection = self.aggregate.connections.get
        while True:
            connection = get_connection(scheme, host, port, create_connection)
            if hasattr(connection, 'acquire'):
                # This little trick avoids polling: wait for another
                # connection to be released.
                connection.acquire()
                # The lock is immediately released since the above call to
                # connections.get() acquires it again.
                connection.release()
            else:
                self.url_connection = connection
                break
