# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2008 Bastian Kleineidam
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
Aggregate needed object instances for checker threads.
"""
import time
import threading
from .. import log, LOG_CHECK
from ..decorators import synchronized
from ..cache import urlqueue
from . import logger, status, checker, cleanup


_lock = threading.Lock()

class Aggregate (object):
    """Store thread-safe data collections for checker threads."""

    def __init__ (self, config, urlqueue, connections, cookies, robots_txt):
        self.config = config
        self.urlqueue = urlqueue
        self.connections = connections
        self.cookies = cookies
        self.robots_txt = robots_txt
        self.logger = logger.Logger(config)
        self.threads = []
        self.last_w3_call = 0

    def start_threads (self):
        """Spawn threads for URL checking and status printing."""
        if self.config["status"]:
            t = status.Status(self.urlqueue)
            t.start()
            self.threads.append(t)
        t = cleanup.Cleanup(self.connections)
        t.start()
        self.threads.append(t)
        num = self.config["threads"]
        if num >= 1:
            for dummy in xrange(num):
                t = checker.Checker(self.urlqueue, self.logger)
                t.start()
                self.threads.append(t)
        else:
            checker.check_url(self.urlqueue, self.logger)

    def abort (self):
        """Empty the URL queue."""
        self.urlqueue.do_shutdown()
        try:
            self.urlqueue.join(timeout=self.config["timeout"])
        except urlqueue.Timeout:
            log.warn(LOG_CHECK, "Abort timed out")

    def remove_stopped_threads (self):
        "Remove the stopped threads from the internal thread list."""
        self.threads = [t for t in self.threads if t.isAlive()]

    def finish (self):
        """Wait for checker threads to finish."""
        assert self.urlqueue.empty()
        for t in self.threads:
            t.stop()
            t.join(2)
            if t.isAlive():
                log.warn(LOG_CHECK, "Thread %s still active", t)
        self.connections.clear()

    @synchronized(_lock)
    def check_w3_time (self):
        """Make sure the W3C validators are at most called once a second."""
        if time.time() - self.last_w3_call < 1:
            time.sleep(1)
        self.last_w3_call = time.time()
