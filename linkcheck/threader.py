# -*- coding: iso-8859-1 -*-
"""Threading support"""
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
import time
try:
    import threading
except ImportError:
    import dummy_threading as threading


class Threader (object):
    """
    A thread generating class.
    """

    def __init__ (self, num=5):
        """
        Store maximum number of threads to generate, and initialize
        an empty thread list.
        """
        # this allows negative numbers
        self.threads_max = max(num, 1)
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
        # XXX don't know how to stop a thread

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
