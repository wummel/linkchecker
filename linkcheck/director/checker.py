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
"""
URL checking functions.
"""
import copy
from . import task
from ..cache import urlqueue


def check_url (urlqueue, logger):
    """Check URLs without threading."""
    while not urlqueue.empty():
        url_data = urlqueue.get()
        try:
            if not url_data.has_result:
                url_data.check()
            logger.log_url(url_data.to_wire())
        finally:
            urlqueue.task_done(url_data)


class Checker (task.LoggedCheckedTask):
    """URL check thread."""

    def __init__ (self, urlqueue, logger, add_request_session):
        """Store URL queue and logger."""
        super(Checker, self).__init__(logger)
        self.urlqueue = urlqueue
        self.origname = self.getName()
        self.add_request_session = add_request_session

    def run_checked (self):
        """Check URLs in the queue."""
        # construct per-thread HTTP/S requests session
        self.add_request_session()
        while not self.stopped(0):
            self.check_url()

    def check_url (self):
        """Try to get URL data from queue and check it."""
        try:
            url_data = self.urlqueue.get(timeout=0.2)
            if url_data is not None:
                try:
                    self.check_url_data(url_data)
                finally:
                    self.urlqueue.task_done(url_data)
                self.setName(self.origname)
        except urlqueue.Empty:
            pass

    def check_url_data (self, url_data):
        """Check one URL data instance."""
        if url_data.url is None:
            url = ""
        else:
            url = url_data.url.encode("ascii", "replace")
        self.setName("CheckThread-%s" % url)
        if url_data.has_result:
            self.logger.log_url(url_data.to_wire())
        else:
            cache = url_data.aggregate.result_cache
            key = url_data.cache_key[1]
            result = cache.get_result(key)
            if result is None:
                url_data.check()
                result = url_data.to_wire()
                cache.add_result(key, result)
            else:
                result = copy.copy(result)
                result.parent_url = url_data.parent_url
            self.logger.log_url(result)
