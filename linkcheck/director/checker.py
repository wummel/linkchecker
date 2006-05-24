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
import time
import Queue
import task


def check_url (urlqueue, logger):
    """
    Check URLs without threading.
    """
    while not urlqueue.empty():
        url_data = urlqueue.get()
        try:
            if not url_data.has_result:
                url_data.check()
            logger.log_url(url_data)
        finally:
            urlqueue.task_done(url_data)


class Checker (task.CheckedTask):
    """
    URL check thread.
    """

    def __init__ (self, urlqueue, logger):
        """
        Store URL queue and logger.
        """
        super(Checker, self).__init__()
        self.urlqueue = urlqueue
        self.logger = logger
        self.origname = self.getName()

    def run_checked (self):
        """
        Check URLs in the queue.
        """
        while True:
            self.check_url()
            if self.stopped():
                return

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
            self.setName(self.origname)

    def check_url_data (self, url_data):
        """
        Check one URL data instance.
        """
        try:
            if url_data.url is None:
                url = ""
            else:
                url = url_data.url.encode("ascii", "replace")
            self.setName("Thread-%s" % url)
            if not url_data.has_result:
                url_data.check()
            self.logger.log_url(url_data)
        finally:
            self.urlqueue.task_done(url_data)
