# -*- coding: iso-8859-1 -*-
"""url consumer class"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import sys
import time
try:
    import threading
except ImportError:
    import dummy_threading as threading

import linkcheck.threader
import linkcheck.log
from urlbase import stderr

class Consumer (object):
    """consume urls from the url queue in a threaded manner"""

    def __init__ (self, config, cache):
        """initialize consumer data and threads"""
        self.config = config
        self.cache = cache
        self.threader = linkcheck.threader.Threader()
        self._set_threads(config['threads'])
        self.logger = config['logger']
        self.fileoutput = config['fileoutput']
        self.linknumber = 0
        # one lock for the data
        self.lock = threading.Lock()
        # if checking had errors
        self.errors = False
        # if checking had warnings
        self.warnings = False

    def _set_threads (self, num):
        """set number of checker threads to start"""
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "set threading with %d threads", num)
        self.threader.threads_max = num
        if num > 0:
            sys.setcheckinterval(50)
        else:
            sys.setcheckinterval(100)

    def append_url (self, url_data):
        """append url to incoming check list"""
        if not self.cache.incoming_add(url_data):
            # can be logged
            self.logger_new_url(url_data)

    def check_url (self):
        """start new thread checking the given url"""
        url_data = self.cache.incoming_get_url()
        if url_data is None:
            # active connections are downloading/parsing, so
            # wait a little
            time.sleep(0.1)
        elif url_data.cached:
            # was cached -> can be logged
            self.logger_new_url(url_data)
        else:
            # go check this url
            # this calls either self.checked() or self.interrupted()
            self.threader.start_thread(url_data.check, ())

    def checked (self, url_data):
        """put checked url in cache and log it"""
        # log before putting it in the cache (otherwise we would see
        # a "(cached)" after every url
        self.logger_new_url(url_data)
        if not url_data.cached:
            self.cache.checked_add(url_data)
        else:
            self.cache.in_progress_remove(url_data)

    def interrupted (self, url_data):
        """remove url from active list"""
        self.cache.in_progress_remove(url_data)

    def finished (self):
        """return True if checking is finished"""
        self.lock.acquire()
        try:
            return self.threader.finished() and \
                   self.cache.incoming_len() <= 0
        finally:
            self.lock.release()

    def no_more_threads (self):
        """return True if no more active threads are running"""
        self.lock.acquire()
        try:
            return self.threader.finished()
        finally:
            self.lock.release()

    def abort (self):
        """abort checking and send of-of-output message to logger"""
        while not self.no_more_threads():
            linkcheck.log.warn(linkcheck.LOG_CHECK,
             _("keyboard interrupt; waiting for %d active threads to finish"),
             self.active_threads())
            self.lock.acquire()
            try:
                self.threader.finish()
            finally:
                self.lock.release()
            time.sleep(2)
        self.logger_end_output()

    def print_status (self, curtime, start_time):
        """print check status looking at url queues"""
        self.lock.acquire()
        try:
            active = self.threader.active_threads()
            links = self.linknumber
            tocheck = self.cache.incoming_len()
            duration = linkcheck.strformat.strduration(curtime - start_time)
            print >> stderr, _("Status: %5d URLs queued, "
                     "%4d URLs checked, %2d active threads, runtime %s") % \
                                 (tocheck, links, active, duration)
        finally:
            self.lock.release()

    def logger_start_output (self):
        """start output of all configured loggers"""
        self.lock.acquire()
        try:
             self.logger.start_output()
            for logger in self.fileoutput:
                logger.start_output()
        finally:
            self.lock.release()

    def logger_new_url (self, url_data):
        """send new url to all configured loggers"""
        self.lock.acquire()
        try:
            self.linknumber += 1
            do_filter = (self.linknumber % 1000) == 0
            if not url_data.valid:
                self.errors = True
            if url_data.warning and self.config["warnings"]:
                self.warnings = True
            if (self.config["verbose"] or not url_data.valid or
                (url_data.warning and self.config["warnings"])):
                self.logger.new_url(url_data)
                for log in self.fileoutput:
                    log.new_url(url_data)
        finally:
            self.lock.release()
        # XXX deadlock!
        #if do_filter:
        #    self.filter_queue(self)

    def logger_end_output (self):
        """end output of all configured loggers"""
        self.lock.acquire()
        try:
            self.logger.end_output(linknumber=self.linknumber)
            for logger in self.fileoutput:
                logger.end_output(linknumber=self.linknumber)
        finally:
            self.lock.release()

    def active_threads (self):
        """return number of active threads"""
        self.lock.acquire()
        try:
            return self.threader.active_threads()
        finally:
            self.lock.release()

