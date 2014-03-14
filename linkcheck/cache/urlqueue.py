# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
Handle a queue of URLs to check.
"""
import threading
import collections
from time import time as _time
from .. import log, LOG_CACHE


class Timeout (StandardError):
    """Raised by join()"""
    pass

class Empty (StandardError):
    """Exception raised by get()."""
    pass


NUM_PUTS_CLEANUP = 10000

class UrlQueue (object):
    """A queue supporting several consumer tasks. The task_done() idea is
    from the Python 2.5 implementation of Queue.Queue()."""

    def __init__ (self, max_allowed_urls=None):
        """Initialize the queue state and task counters."""
        # Note: don't put a maximum size on the queue since it would
        # lead to deadlocks when all worker threads called put().
        self.queue = collections.deque()
        # mutex must be held whenever the queue is mutating.  All methods
        # that acquire mutex must release it before returning.  mutex
        # is shared between the two conditions, so acquiring and
        # releasing the conditions also acquires and releases mutex.
        self.mutex = threading.Lock()
        # Notify not_empty whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.not_empty = threading.Condition(self.mutex)
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0
        self.finished_tasks = 0
        self.in_progress = 0
        self.shutdown = False
        # Each put() decreases the number of allowed puts.
        # This way we can restrict the number of URLs that are checked.
        if max_allowed_urls is not None and max_allowed_urls <= 0:
            raise ValueError("Non-positive number of allowed URLs: %d" % max_allowed_urls)
        self.max_allowed_urls = max_allowed_urls
        self.num_puts = 0

    def qsize (self):
        """Return the approximate size of the queue (not reliable!)."""
        with self.mutex:
            return len(self.queue)

    def empty (self):
        """Return True if the queue is empty, False otherwise.
        Result is thread-safe, but not reliable since the queue could have
        been changed before the result is returned!"""
        with self.mutex:
            return self._empty()

    def _empty (self):
        """Return True if the queue is empty, False otherwise.
        Not thread-safe!"""
        return not self.queue

    def get (self, timeout=None):
        """Get first not-in-progress url from the queue and
        return it. If no such url is available return None.
        """
        with self.not_empty:
            return self._get(timeout)

    def _get (self, timeout):
        """Non thread-safe utility function of self.get() doing the real
        work."""
        if timeout is None:
            while self._empty():
                self.not_empty.wait()
        else:
            if timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            endtime = _time() + timeout
            while self._empty():
                remaining = endtime - _time()
                if remaining <= 0.0:
                    raise Empty()
                self.not_empty.wait(remaining)
        self.in_progress += 1
        return self.queue.popleft()

    def put (self, item):
        """Put an item into the queue.
        Block if necessary until a free slot is available.
        """
        with self.mutex:
            self._put(item)
            self.not_empty.notify()

    def _put (self, url_data):
        """Put URL in queue, increase number of unfished tasks."""
        if self.shutdown or self.max_allowed_urls == 0:
            return
        log.debug(LOG_CACHE, "queueing %s", url_data.url)
        key = url_data.cache_url
        cache = url_data.aggregate.result_cache
        if url_data.has_result or cache.has_result(key):
            self.queue.appendleft(url_data)
        else:
            assert key is not None, "no result for None key: %s" % url_data
            if self.max_allowed_urls is not None:
                self.max_allowed_urls -= 1
            self.num_puts += 1
            if self.num_puts >= NUM_PUTS_CLEANUP:
                self.cleanup()
            self.queue.append(url_data)
        self.unfinished_tasks += 1

    def cleanup(self):
        """Move cached elements to top."""
        self.num_puts = 0
        cached = []
        for i, url_data in enumerate(self.queue):
            key = url_data.cache_url
            cache = url_data.aggregate.result_cache
            if cache.has_result(key):
                cached.append(i)
        for pos in cached:
            self._move_to_top(pos)

    def _move_to_top(self, pos):
        """Move element at given position to top of queue."""
        if pos > 0:
            self.queue.rotate(-pos)
            item = self.queue.popleft()
            self.queue.rotate(pos)
            self.queue.appendleft(item)

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
        with self.all_tasks_done:
            log.debug(LOG_CACHE, "task_done %s", url_data.url)
            self.finished_tasks += 1
            self.unfinished_tasks -= 1
            self.in_progress -= 1
            if self.unfinished_tasks <= 0:
                if self.unfinished_tasks < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notifyAll()

    def join (self, timeout=None):
        """Blocks until all items in the Queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved and all work on it is complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        with self.all_tasks_done:
            if timeout is None:
                while self.unfinished_tasks:
                    self.all_tasks_done.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = _time() + timeout
                while self.unfinished_tasks:
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Timeout()
                    self.all_tasks_done.wait(remaining)

    def do_shutdown (self):
        """Shutdown the queue by not accepting any more URLs."""
        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            self.queue.clear()
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('shutdown is in error')
                self.all_tasks_done.notifyAll()
            self.unfinished_tasks = unfinished
            self.shutdown = True

    def status (self):
        """Get tuple (finished tasks, in progress, queue size)."""
        # no need to acquire self.mutex since the numbers are unreliable anyways.
        return (self.finished_tasks, self.in_progress, len(self.queue))
