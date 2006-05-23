# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
Handle a queue of URLs to check.
"""
import threading
import Queue
import time
import linkcheck
import linkcheck.log


class Timeout (StandardError):
    """Raised by join()"""
    pass


class UrlQueue (Queue.Queue):
    """
    A queue supporting several consumer tasks. The task_done() idea is
    from the Python 2.5 Subversion repository.
    """

    def __init__ (self):
        """
        Initialize the queue state and task counters.
        """
        # Note: don't put a maximum size on the queue since it would
        # lead to deadlocks when all worker threads called put().
        Queue.Queue.__init__(self)
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0
        self.finished_tasks = 0
        self.in_progress = {}
        self.checked = {}
        self.shutdown = False

    def get (self, timeout=None):
        """
        Get first not-in-progress url from the queue and
        return it. If no such url is available return None. The
        url might be already cached.
        """
        self.not_empty.acquire()
        try:
            if timeout is None:
                while self._empty():
                    self.not_empty.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = time.time() + timeout
                while self._empty():
                    remaining = endtime - time.time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            url_data = self._get()
            key = url_data.cache_url_key
            if url_data.has_result:
                # Already checked and copied from cache.
                pass
            elif key in self.checked:
                # Already checked; copy result. And even ignore
                # the case where url happens to be in_progress.
                url_data.copy_from_cache(self.checked[key])
            elif key in self.in_progress:
                # It's being checked currently; put it back in the queue.
                Queue.Queue._put(self, url_data)
                url_data = None
            else:
                self.in_progress[key] = url_data
            self.not_full.notify()
            return url_data
        finally:
            self.not_empty.release()

    def _put (self, url_data):
        """
        Put URL in queue, increase number of unfished tasks.
        """
        if self.shutdown:
            # don't accept more URLs
            return
        assert None == linkcheck.log.debug(linkcheck.LOG_CACHE,
            "queueing %s", url_data)
        key = url_data.cache_url_key
        if key in self.checked:
            # Put at beginning of queue to get consumed quickly.
            url_data.copy_from_cache(self.checked[key])
            self.queue.appendleft(url_data)
        elif key in self.in_progress:
            # Put at beginning of queue since it will be cached soon.
            self.queue.appendleft(url_data)
        else:
            self.queue.append(url_data)
        self.unfinished_tasks += 1

    def task_done (self, url_data):
        """
        Indicate that a formerly enqueued task is complete.

        Used by Queue consumer threads.  For each get() used to fetch a task,
        a subsequent call to task_done() tells the queue that the processing
        on the task is complete.

        If a join() is currently blocking, it will resume when all items
        have been processed (meaning that a task_done() call was received
        for every item that had been put() into the queue).

        Raises a ValueError if called more times than there were items
        placed in the queue.
        """
        self.all_tasks_done.acquire()
        try:
            assert None == linkcheck.log.debug(linkcheck.LOG_CACHE,
                "task_done %s", url_data)
            if url_data is not None:
                key = url_data.cache_url_key
                if key is not None and key not in self.checked:
                    self._cache_url(key, url_data)
                else:
                    assert key not in self.in_progress
            self.finished_tasks += 1
            unfinished = self.unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notifyAll()
            self.unfinished_tasks = unfinished
        finally:
            self.all_tasks_done.release()

    def _cache_url (self, key, url_data):
        """
        Put URL result data into cache.
        """
        assert None == linkcheck.log.debug(linkcheck.LOG_CACHE,
            "Caching %r", key)
        assert key in self.in_progress, \
            "%r not in %s" % (key, self.in_progress)
        del self.in_progress[key]
        data = url_data.get_cache_data()
        self.checked[key] = data
        # check for aliases (eg. through HTTP redirections)
        if hasattr(url_data, "aliases"):
            data = url_data.get_alias_cache_data()
            for key in url_data.aliases:
                if key in self.checked or key in self.in_progress:
                    continue
                assert None == linkcheck.log.debug(linkcheck.LOG_CACHE,
                    "Caching alias %r", key)
                self.checked[key] = data

    def join (self, timeout=None):
        """Blocks until all items in the Queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved and all work on it is complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        self.all_tasks_done.acquire()
        try:
            if timeout is None:
                while self.unfinished_tasks:
                    self.all_tasks_done.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = time.time() + timeout
                while self.unfinished_tasks:
                    remaining = endtime - time.time()
                    if remaining <= 0.0:
                        raise Timeout()
                    self.all_tasks_done.wait(remaining)
        finally:
            self.all_tasks_done.release()

    def do_shutdown (self):
        """
        Shutdown the queue by not accepting any more URLs.
        """
        self.mutex.acquire()
        try:
            unfinished = self.unfinished_tasks - len(self.queue)
            self.queue.clear()
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('shutdown is in error')
                self.all_tasks_done.notifyAll()
            self.unfinished_tasks = unfinished
            self.shutdown = True
        finally:
            self.mutex.release()

    def status (self):
        """
        Get tuple (finished tasks, in progress, queue size).
        """
        self.mutex.acquire()
        try:
            return (self.finished_tasks,
                    len(self.in_progress), len(self.queue))
        finally:
            self.mutex.release()

    def checked_redirect (self, redirect, url_data):
        """
        Check if redirect is already in cache. Used for URL redirections
        to avoid double checking of already cached URLs.
        If the redirect URL is found in the cache, the result data is
        already copied.
        """
        self.mutex.acquire()
        try:
            if redirect in self.checked:
                url_data.copy_from_cache(self.checked[redirect])
                return True
            return False
        finally:
            self.mutex.release()
