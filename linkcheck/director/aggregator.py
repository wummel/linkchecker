# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2007 Bastian Kleineidam
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
"""Aggregate needed object instances for checker threads."""
import linkcheck.log
import linkcheck.director
import logger
import status
import checker


class Aggregate (object):
    """
    Store thread-safe data collections for checker threads.
    """

    def __init__ (self, config, urlqueue, connections, cookies, robots_txt):
        self.config = config
        self.urlqueue = urlqueue
        self.connections = connections
        self.cookies = cookies
        self.robots_txt = robots_txt
        self.logger = logger.Logger(config)
        self.threads = []

    def start_threads (self):
        """
        Spawn threads for URL checking and status printing.
        """
        if self.config["status"]:
            t = status.Status(self.urlqueue)
            t.start()
            self.threads.append(t)
        num = self.config["threads"]
        if num >= 1:
            for i in xrange(num):
                t = checker.Checker(self.urlqueue, self.logger)
                t.start()
                self.threads.append(t)
        else:
            checker.check_url(self.urlqueue, self.logger)

    def abort (self):
        """
        Empty the URL queue.
        """
        self.urlqueue.do_shutdown()
        try:
            self.urlqueue.join(timeout=self.config["timeout"])
        except linkcheck.cache.urlqueue.Timeout:
            linkcheck.log.warn(linkcheck.LOG_CHECK, "Abort timed out")

    def remove_stopped_threads (self):
        self.threads = [t for t in self.threads if t.isAlive()]

    def finish (self):
        """
        Wait for checker threads to finish.
        """
        assert self.urlqueue.empty()
        for t in self.threads:
            t.stop()
            t.join(2)
            if t.isAlive():
                linkcheck.log.warn(linkcheck.LOG_CHECK, "Thread %s still active", t)
