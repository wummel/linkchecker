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
Support for managing threads.
"""

import time
import os
try:
    import threading
except ImportError:
    import dummy_threading as threading

try:
    import win32process
    _has_win32process = True
except ImportError:
    _has_win32process = False

# generic thread priorities with mappings to Windows and Unix
# priority values
PRIO_HIGH = 0
PRIO_NORMAL = 1
PRIO_LOW = 2

_posix_nice_val = {
    PRIO_HIGH: -5,
    PRIO_NORMAL: +0,
    PRIO_LOW: +10,
}
if _has_win32process:
    if hasattr(win32process, "BELOW_NORMAL_PRIORITY_CLASS"):
        _low = win32process.BELOW_NORMAL_PRIORITY_CLASS
    else:
        _low = win32process.IDLE_PRIORITY_CLASS
    if hasattr(win32process, "ABOVE_NORMAL_PRIORITY_CLASS"):
        _high = win32process.ABOVE_NORMAL_PRIORITY_CLASS
    else:
        _high = win32process.HIGH_PRIORITY_CLASS
    _nt_prio_val = {
        PRIO_HIGH: _high,
        PRIO_NORMAL: win32process.NORMAL_PRIORITY_CLASS,
        PRIO_LOW: _low,
    }


def set_thread_priority (prio):
    """
    Set priority of this thread (and thus also for all spawned threads).
    """
    if os.name == 'nt' and _has_win32process:
        res = win32process.SetPriorityClass(
                   win32process.GetCurrentProcess(), _nt_prio_val[prio])
    elif os.name == 'posix':
        res = os.nice(_posix_nice_val[prio])
    else:
        res = None
    return res


class Threader (object):
    """
    A thread generating class. Note that since Python has no ability to
    stop threads from outside, one has to make sure threads poll
    regularly for outside variables to stop them. Or one makes sure
    threads surely will terminate in finite time.
    """

    def __init__ (self, num=5):
        """
        Store maximum number of threads to generate, and initialize
        an empty thread list.
        """
        # this allows negative numbers
        self.threads_max = max(num, 0)
        # list of active threads to watch
        self.threads = []

    def _acquire (self):
        """
        Wait until we are allowed to start a new thread.
        """
        while self.active_threads() >= self.threads_max:
            self._reduce_threads()
            time.sleep(0.1)

    def _reduce_threads (self):
        """
        Remove inactive threads.
        """
        self.threads = [ t for t in self.threads if t.isAlive() ]

    def active_threads (self):
        """
        Return number of active threads.
        """
        return len(self.threads)

    def finished (self):
        """
        Return True if no active threads are left.
        """
        if self.threads_max > 0:
            self._reduce_threads()
        return self.active_threads() == 0

    def finish (self):
        """
        Remove inactive threads.
        """
        self._reduce_threads()

    def start_thread (self, func, args):
        """
        Generate a new thread.
        """
        if self.threads_max < 1:
            # threading is disabled
            func(*args)
        else:
            self._acquire()
            t = threading.Thread(None, func, None, args)
            t.start()
            self.threads.append(t)

    def __str__ (self):
        """
        String representation of threader state.
        """
        return "Threader with %d threads (max %d)" % \
            (self.active_threads(), self.threads_max)


