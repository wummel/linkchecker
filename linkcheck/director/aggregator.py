# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
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
import Queue
import thread
import threading
import time
import logger
import status
import linkcheck
import linkcheck.log
import linkcheck.director


def check_target (target, args):
    """
    Wrapper function calling target() while catching keyboard
    interrupt and errors.
    """
    try:
        target(*args)
    except KeyboardInterrupt:
        linkcheck.log.warn(linkcheck.LOG_CHECK,
            "interrupt did not reach the main thread")
        thread.interrupt_main()
    except StandardError:
        status.internal_error()


def start_thread (target, *args):
    """
    Spawn a new subthread executing target().
    """
    t = threading.Thread(target=lambda: check_target(target, args))
    t.setDaemon(True)
    t.start()
    return t


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
            t = start_thread(status.do_status, self.urlqueue)
            self.threads.append(t)
        num = self.config["threads"]
        if num >= 1:
            for i in xrange(num):
                t = start_thread(self.worker)
                self.threads.append(t)
        else:
            self.worker()

    def worker (self):
        """
        Check URLs from queue until finished.
        """
        name = threading.currentThread().getName()
        while True:
            self.check_url()
            threading.currentThread().setName(name)
            if self.urlqueue.empty():
                break

    def check_url (self):
        """
        Try to get URL data from queue and check it.
        """
        try:
            url_data = self.urlqueue.get(timeout=1)
        except Queue.Empty:
            time.sleep(1)
            return
        if url_data is not None:
            self.check_url_data(url_data)

    def check_url_data (self, url_data):
        """
        Check one URL data instance.
        """
        try:
            url = url_data.url.encode("ascii", "replace")
            threading.currentThread().setName("Thread-%s" % url)
            if not url_data.has_result:
                url_data.check()
            self.logger.log_url(url_data)
        finally:
            self.urlqueue.task_done(url_data)

    def abort (self):
        """
        Empty the URL queue.
        """
        self.urlqueue.do_shutdown()
        try:
            self.urlqueue.join(timeout=self.config["timeout"])
        except linkcheck.cache.urlqueue.Timeout:
            linkcheck.log.warn(linkcheck.LOG_CHECK, "Abort timed out")

    def finish (self):
        """
        Wait for checker threads to finish.
        """
        assert self.urlqueue.empty()
        if self.config["status"]:
            status.disable_status()
        for t in self.threads:
            t.join(2)
            if t.isAlive():
                linkcheck.log.warn(linkcheck.LOG_CHECK, "Thread %s still active", t)
