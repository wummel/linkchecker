# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2010 Bastian Kleineidam
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
"""Status message handling"""
import time
from . import task


class Status (task.CheckedTask):
    """Status thread."""

    def __init__ (self, urlqueue, logger, wait_seconds):
        """Store urlqueue object."""
        super(Status, self).__init__()
        self.urlqueue = urlqueue
        self.logger = logger
        self.wait_seconds = wait_seconds

    def run_checked (self):
        """Print periodic status messages."""
        self.start_time = time.time()
        self.setName("Status")
        waitfor = range(self.wait_seconds*10)
        while True:
            for dummy in waitfor:
                time.sleep(0.1)
                if self.stopped():
                    return
            self.log_status()

    def log_status (self):
        """Log a status message."""
        duration = time.time() - self.start_time
        checked, in_progress, queue = self.urlqueue.status()
        self.logger.log_status(checked, in_progress, queue, duration)
