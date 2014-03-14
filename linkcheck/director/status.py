# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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


class Status (task.LoggedCheckedTask):
    """Thread that gathers and logs the status periodically."""

    def __init__ (self, aggregator, wait_seconds):
        """Initialize the status logger task.
        @param urlqueue: the URL queue
        @ptype urlqueue: Urlqueue
        @param logger: the logger object to inform about status
        @ptype logger: console.StatusLogger
        @param wait_seconds: interval in seconds to report status
        @ptype wait_seconds: int
        """
        logger = aggregator.config.status_logger
        super(Status, self).__init__(logger)
        self.aggregator = aggregator
        self.wait_seconds = wait_seconds
        assert self.wait_seconds >= 1

    def run_checked (self):
        """Print periodic status messages."""
        self.start_time = time.time()
        self.setName("Status")
        # the first status should be after a second
        wait_seconds = 1
        first_wait = True
        while not self.stopped(wait_seconds):
            self.log_status()
            if first_wait:
                wait_seconds = self.wait_seconds
                first_wait = False

    def log_status (self):
        """Log a status message."""
        duration = time.time() - self.start_time
        checked, in_progress, queue = self.aggregator.urlqueue.status()
        num_urls = len(self.aggregator.result_cache)
        self.logger.log_status(checked, in_progress, queue, duration, num_urls)
