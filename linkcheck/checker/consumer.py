# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
Url consumer class.
"""

import sys
import time

import linkcheck.threader
import linkcheck.log
import linkcheck.lock
import linkcheck.strformat
import linkcheck.checker.geoip
from urlbase import stderr


def print_tocheck (tocheck):
    msg = _n("%5d URL queued,", "%5d URLs queued,", tocheck) % tocheck
    print >> stderr, msg,


def print_links (links):
    msg = _n("%4d URL checked,", "%4d URLs checked,", links) % links
    print >> stderr, msg,


def print_active (active):
    msg = _n("%2d active thread,", "%2d active threads,", active) % active
    print >> stderr, msg,


def print_duration (duration):
    msg = _("runtime %s") % linkcheck.strformat.strduration(duration)
    print >> stderr, msg,


class Consumer (linkcheck.lock.AssertLock):
    """
    Consume urls from the url queue in a thread-safe manner.
    """

    def __init__ (self, config, cache):
        """
        Initialize consumer data and threads.
        """
        super(Consumer, self).__init__()
        self.config = config
        self.cache = cache
        self.threader = linkcheck.threader.Threader(num=config['threads'])
        self.logger = config['logger']
        self.fileoutput = config['fileoutput']
        self.logger_start_output()

    def append_url (self, url_data):
        """
        Append url to incoming check list.
        """
        if not self.cache.incoming_add(url_data):
            # can be logged
            self.logger_log_url(url_data)

    def check_url (self):
        """
        Start new thread checking the given url.
        """
        url_data = self.cache.incoming_get_url()
        if url_data is None:
            # active connections are downloading/parsing, so
            # wait a little
            time.sleep(0.1)
        elif url_data.cached:
            # was cached -> can be logged
            self.logger_log_url(url_data)
        else:
            # go check this url
            # this calls either self.checked() or self.interrupted()
            self.threader.start_thread(url_data.check, ())

    def checked (self, url_data):
        """
        Put checked url in cache and log it.
        """
        # log before putting it in the cache (otherwise we would see
        # a "(cached)" after every url
        self.logger_log_url(url_data)
        if not url_data.cached:
            self.cache.checked_add(url_data)
        else:
            self.cache.in_progress_remove(url_data)

    def interrupted (self, url_data):
        """
        Remove url from active list.
        """
        self.cache.in_progress_remove(url_data, ignore_missing=True)

    def finished (self):
        """
        Return True if checking is finished.
        """
        # avoid deadlock by requesting cache data before locking
        tocheck = self.cache.incoming_len()
        self.acquire()
        try:
            return self.threader.finished() and tocheck <= 0
        finally:
            self.release()

    def no_more_threads (self):
        """
        Return True if no more active threads are running.
        """
        self.acquire()
        try:
            return self.threader.finished()
        finally:
            self.release()

    def abort (self):
        """
        Abort checking and send end-of-output message to logger.
        """
        # wait for threads to finish
        while not self.no_more_threads():
            num = self.active_threads()
            msg = \
            _n("keyboard interrupt; waiting for %d active thread to finish",
               "keyboard interrupt; waiting for %d active threads to finish",
               num)
            linkcheck.log.warn(linkcheck.LOG_CHECK, msg, num)
            self.acquire()
            try:
                self.threader.finish()
            finally:
                self.release()
            time.sleep(2)
        self.logger_end_output()

    def print_status (self, curtime, start_time):
        """
        Print check status looking at url queues.
        """
        # avoid deadlock by requesting cache data before locking
        tocheck = self.cache.incoming_len()
        self.acquire()
        try:
            print >> stderr, _("Status:"),
            active = self.threader.active_threads()
            print_active(active)
            print_links(self.logger.number)
            print_tocheck(tocheck)
            print_duration(curtime - start_time)
            print >> stderr
        finally:
            self.release()

    def logger_start_output (self):
        """
        Start output of all configured loggers.
        """
        self.acquire()
        try:
            self.logger.start_output()
            for logger in self.fileoutput:
                logger.start_output()
        finally:
            self.release()

    def logger_log_url (self, url_data):
        """
        Send new url to all configured loggers.
        """
        self.acquire()
        try:
            do_print = self.config["verbose"] or not url_data.valid or \
                (url_data.warning and self.config["warnings"])
            self.logger.log_filter_url(url_data, do_print)
            for log in self.fileoutput:
                log.log_filter_url(url_data, do_print)
        finally:
            self.release()
        # do_filter = (self.linknumber % 1000) == 0
        # XXX deadlock!
        #if do_filter:
        #    self.filter_queue(self)

    def logger_end_output (self):
        """
        End output of all configured loggers.
        """
        self.acquire()
        try:
            self.logger.end_output()
            for logger in self.fileoutput:
                logger.end_output()
        finally:
            self.release()

    def active_threads (self):
        """
        Return number of active threads.
        """
        self.acquire()
        try:
            return self.threader.active_threads()
        finally:
            self.release()

    def get_country_name (self, host):
        """
        Return country code for host if found, else None.
        """
        self.acquire()
        try:
            gi = self.config["geoip"]
            if gi:
                return linkcheck.checker.geoip.get_country(gi, host)
            return None
        finally:
            self.release()
