# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
Locking utility class.
"""
import threading
from . import log, LOG_THREAD

def get_lock (name, debug=False):
    """Get a new lock.
    @param debug: if True, acquire() and release() will have debug messages
    @ptype debug: boolean, default is False
    @return: a lock object
    @rtype: threading.Lock or DebugLock
    """
    lock = threading.Lock()
    # for thread debugging, use the DebugLock wrapper
    if debug:
        lock = DebugLock(lock, name)
    return lock


class DebugLock (object):
    """Debugging lock class."""

    def __init__ (self, lock, name):
        """Store lock and name parameters."""
        self.lock = lock
        self.name = name

    def acquire (self, blocking=1):
        """Acquire lock."""
        threadname = threading.currentThread().getName()
        log.debug(LOG_THREAD, "Acquire %s for %s", self.name, threadname)
        self.lock.acquire(blocking)
        log.debug(LOG_THREAD, "...acquired %s for %s", self.name, threadname)

    def release (self):
        """Release lock."""
        threadname = threading.currentThread().getName()
        log.debug(LOG_THREAD, "Release %s for %s", self.name, threadname)
        self.lock.release()


def get_semaphore(name, value=None, debug=False):
    """Get a new semaphore.
    @param value: if not None, a BoundedSemaphore will be used
    @ptype debug: int or None
    @param debug: if True, acquire() and release() will have debug messages
    @ptype debug: boolean, default is False
    @return: a semaphore object
    @rtype: threading.Semaphore or threading.BoundedSemaphore or DebugLock
    """
    if value is None:
        lock = threading.Semaphore()
    else:
        lock = threading.BoundedSemaphore(value)
    if debug:
        lock = DebugLock(lock, name)
    return lock
