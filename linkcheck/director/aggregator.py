# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2012 Bastian Kleineidam
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
Aggregate needed object instances for checker threads.
"""
import time
import threading
from .. import log, LOG_CHECK
from ..decorators import synchronized
from ..cache import urlqueue
from . import logger, status, checker, cleanup


_w3_time_lock = threading.Lock()
_threads_lock = threading.Lock()

class Aggregate (object):
    """Store thread-safe data collections for checker threads."""

    def __init__ (self, config, urlqueue, connections, cookies, robots_txt):
        """Store given link checking objects."""
        self.config = config
        self.urlqueue = urlqueue
        self.connections = connections
        self.cookies = cookies
        self.robots_txt = robots_txt
        self.logger = logger.Logger(config)
        self.threads = []
        self.last_w3_call = 0

    @synchronized(_threads_lock)
    def start_threads (self):
        """Spawn threads for URL checking and status printing."""
        if self.config["status"]:
            t = status.Status(self.urlqueue, self.config.status_logger,
                self.config["status_wait_seconds"])
            t.start()
            self.threads.append(t)
        t = cleanup.Cleanup(self.connections)
        t.start()
        self.threads.append(t)
        num = self.config["threads"]
        if num > 0:
            for dummy in range(num):
                t = checker.Checker(self.urlqueue, self.logger)
                t.start()
                self.threads.append(t)
        else:
            checker.check_url(self.urlqueue, self.logger)

    @synchronized(_threads_lock)
    def print_active_threads (self):
        """Log all currently active threads."""
        first = True
        for name in self._get_check_threads():
            if first:
                log.info(LOG_CHECK, _("These URLs are still active:"))
                first = False
            log.info(LOG_CHECK, name[12:])

    @synchronized(_threads_lock)
    def get_check_threads(self):
        """Return iterator of checker threads."""
        return self._get_check_threads()

    def _get_check_threads(self):
        """Return iterator of checker threads (non-synchronized method)."""
        for t in self.threads:
            name = t.getName()
            if name.startswith("CheckThread-"):
                yield name

    def cancel (self):
        """Empty the URL queue."""
        self.urlqueue.do_shutdown()

    def abort (self):
        """Print still-active URLs and empty the URL queue."""
        self.print_active_threads()
        self.cancel()
        timeout = self.config["timeout"]
        try:
            self.urlqueue.join(timeout=timeout)
        except urlqueue.Timeout:
            log.warn(LOG_CHECK, "Abort timed out after %d seconds, stopping application." % timeout)
            raise KeyboardInterrupt()

    @synchronized(_threads_lock)
    def remove_stopped_threads (self):
        """Remove the stopped threads from the internal thread list."""
        self._remove_stopped_threads()

    def _remove_stopped_threads (self):
        """Not threads-safe function to really remove stopped threads."""
        self.threads = [t for t in self.threads if t.is_alive()]

    @synchronized(_threads_lock)
    def finish (self):
        """Wait for checker threads to finish."""
        if not self.urlqueue.empty():
            # This happens when all checker threads died.
            self.cancel()
        for t in self.threads:
            t.stop()
        self.connections.clear()

    @synchronized(_threads_lock)
    def is_finished (self):
        """Determine if checking is finished."""
        self._remove_stopped_threads()
        return self.urlqueue.empty() and not self.threads

    @synchronized(_w3_time_lock)
    def check_w3_time (self):
        """Make sure the W3C validators are at most called once a second."""
        if time.time() - self.last_w3_call < 1:
            time.sleep(1)
        self.last_w3_call = time.time()
