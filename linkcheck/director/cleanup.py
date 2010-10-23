# -*- coding: iso-8859-1 -*-
# Copyright (C) 2007-2010 Bastian Kleineidam
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
"""Cleanup task."""
import time
from . import task


class Cleanup (task.CheckedTask):
    """Cleanup task performing periodic cleanup of cached connections."""

    def __init__ (self, connections):
        """Store urlqueue object."""
        super(Cleanup, self).__init__()
        self.connections = connections

    def run_checked (self):
        """Print periodic status messages."""
        self.start_time = time.time()
        self.setName("Cleanup")
        # clean every 15 seconds
        wait_seconds = 15
        waitfor = range(wait_seconds*10)
        while True:
            for dummy in waitfor:
                time.sleep(0.1)
                if self.stopped():
                    return
            self.connections.remove_expired()
