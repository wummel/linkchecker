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
try:
    import thread
except ImportError:
    import dummy_thread as thread

import linkcheck.threader
import linkcheck.log
import linkcheck.lock
import linkcheck.strformat
import linkcheck.checker.geoip
from linkcheck.decorators import synchronized
from urlbase import stderr

# global lock for synchronizing all the checker threads
_lock = thread.allocate_lock()


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


class Consumer (object):
    """
    Consume URLs from the URL queue in a thread-safe manner.
    """

    def __init__ (self, config, cache):
        """
        Initialize consumer data and threads.
        """
        super(Consumer, self).__init__()
        self._config = config
        self._cache = cache
        self._threader = linkcheck.threader.Threader(num=config['threads'])
        self.start_log_output()

    @synchronized(_lock)
    def config (self, key):
        return self._config[key]

    @synchronized(_lock)
    def config_append (self, key, val):
        self._config[key].append(val)

    @synchronized(_lock)
    def __getattr__ (self, name):
        if hasattr(self._cache, name):
            return getattr(self._cache, name)
        raise AttributeError(name)

    @synchronized(_lock)
    def append_url (self, url_data):
        """
        Append url to incoming check list.
        """
        if not self._cache.incoming_add(url_data):
            # can be logged
            self._log_url(url_data)

    @synchronized(_lock)
    def check_url (self):
        """
        Start new thread checking the given url.
        """
        url_data = self._cache.incoming_get_url()
        if url_data is None:
            # active connections are downloading/parsing
            pass
        elif url_data.cached:
            # was cached -> can be logged
            self._log_url(url_data)
        else:
            # go check this url
            # this calls either self.checked() or self.interrupted()
            if url_data.parent_url and \
               not linkcheck.url.url_is_absolute(url_data.base_url):
                name = url_data.parent_url
            else:
                name = u""
            name += url_data.base_url
            self._threader.start_thread(url_data.check, (), name=name)
        return url_data and not url_data.cached

    @synchronized(_lock)
    def checked (self, url_data):
        """
        Put checked url in cache and log it.
        """
        # log before putting it in the cache (otherwise we would see
        # a "(cached)" after every url
        self._log_url(url_data)
        if not url_data.cached:
            self._cache.checked_add(url_data)
        else:
            self._cache.in_progress_remove(url_data)

    @synchronized(_lock)
    def interrupted (self, url_data):
        """
        Remove url from active list.
        """
        self._cache.in_progress_remove(url_data, ignore_missing=True)

    @synchronized(_lock)
    def finished (self):
        """
        Return True if checking is finished.
        """
        # avoid deadlock by requesting cache data before locking
        return self._threader.finished() and \
               self._cache.incoming_len() == 0

    @synchronized(_lock)
    def finish (self):
        self._threader.finish()

    @synchronized(_lock)
    def no_more_threads (self):
        """
        Return True if no more active threads are running.
        """
        return self._threader.finished()

    def abort (self):
        """
        Abort checking and send end-of-output message to logger.
        """
        # wait for threads to finish
        num_waited = 0
        wait_max = 30
        while not self.no_more_threads():
            if num_waited > wait_max:
                linkcheck.log.error(linkcheck.LOG_CHECK,
                                    "Thread wait timeout")
                self.end_log_output()
                sys.exit(1)
            num = self.active_threads()
            msg = \
            _n("keyboard interrupt; waiting for %d active thread to finish",
               "keyboard interrupt; waiting for %d active threads to finish",
               num)
            linkcheck.log.warn(linkcheck.LOG_CHECK, msg, num)
            self.finish()
            num_waited += 1
            time.sleep(2)
        self.end_log_output()

    @synchronized(_lock)
    def print_status (self, curtime, start_time):
        """
        Print check status looking at url queues.
        """
        # avoid deadlock by requesting cache data before locking
        print >> stderr, _("Status:"),
        print_active(self._threader.active_threads())
        print_links(self._config['logger'].number)
        print_tocheck(self._cache.incoming_len())
        print_duration(curtime - start_time)
        print >> stderr

    @synchronized(_lock)
    def start_log_output (self):
        """
        Start output of all configured loggers.
        """
        self._config['logger'].start_output()
        for logger in self._config['fileoutput']:
            logger.start_output()

    def _log_url (self, url_data):
        """
        Send new url to all configured loggers.
        """
        do_print = self._config["verbose"] or not url_data.valid or \
            (url_data.warning and self._config["warnings"])
        self._config['logger'].log_filter_url(url_data, do_print)
        for log in self._config['fileoutput']:
            log.log_filter_url(url_data, do_print)
        # do_filter = (self.linknumber % 1000) == 0
        # XXX deadlock!
        #if do_filter:
        #    self.filter_queue(self)

    @synchronized(_lock)
    def end_log_output (self):
        """
        End output of all configured loggers.
        """
        self._config['logger'].end_output()
        for logger in self._config['fileoutput']:
            logger.end_output()

    @synchronized(_lock)
    def active_threads (self):
        """
        Return number of active threads.
        """
        return self._threader.active_threads()

    @synchronized(_lock)
    def get_country_name (self, host):
        """
        Return country code for host if found, else None.
        """
        gi = self._config["geoip"]
        if gi:
            return linkcheck.checker.geoip.get_country(gi, host)
        return None
