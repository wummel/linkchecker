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
import time
from . import task
from ..cache import urlqueue
from .. import parser

# Interval in which each check thread looks if it's stopped.
QUEUE_POLL_INTERVALL_SECS = 1.0


def check_urls (urlqueue, logger):
    """Check URLs without threading."""
    while not urlqueue.empty():
        url_data = urlqueue.get()
        try:
            check_url(url_data, logger)
        finally:
            urlqueue.task_done(url_data)


def check_url(url_data, logger):
    """Check a single URL with logging."""
    if url_data.has_result:
        logger.log_url(url_data.to_wire())
    else:
        cache = url_data.aggregate.result_cache
        key = url_data.cache_url
        result = cache.get_result(key)
        if result is None:
            # check
            check_start = time.time()
            try:
                url_data.check()
                do_parse = url_data.check_content()
                url_data.checktime = time.time() - check_start
                # Add result to cache
                result = url_data.to_wire()
                cache.add_result(key, result)
                for alias in url_data.aliases:
                    # redirect aliases
                    cache.add_result(alias, result)
                # parse content recursively
                # XXX this could add new warnings which should be cached.
                if do_parse:
                    parser.parse_url(url_data)
            finally:
                # close/release possible open connection
                url_data.close_connection()
        else:
            # copy data from cache and adjust it
            result = copy.copy(result)
            result.parent_url = url_data.parent_url
            result.base_ref = url_data.base_ref or u""
            result.base_url = url_data.base_url or u""
            result.line = url_data.line
            result.column = url_data.column
            result.level = url_data.recursion_level
            result.name = url_data.name
        logger.log_url(result)


class Checker(task.LoggedCheckedTask):
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
            url_data = self.urlqueue.get(timeout=QUEUE_POLL_INTERVALL_SECS)
            if url_data is not None:
                try:
                    self.check_url_data(url_data)
                finally:
                    self.urlqueue.task_done(url_data)
                self.setName(self.origname)
        except urlqueue.Empty:
            pass
        except Exception:
            self.internal_error()

    def check_url_data (self, url_data):
        """Check one URL data instance."""
        if url_data.url is None:
            url = ""
        else:
            url = url_data.url.encode("ascii", "replace")
        self.setName("CheckThread-%s" % url)
        check_url(url_data, self.logger)
