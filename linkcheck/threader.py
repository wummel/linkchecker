# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2009 Bastian Kleineidam
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
Support for managing threads.
"""

import os
import threading
try:
    import win32process
    has_win32process = True
except ImportError:
    has_win32process = False
from .containers import enum

# generic thread priorities with mappings to Windows and Unix
# priority values
Prio = enum("high", "normal", "low")

_posix_nice_val = {
    Prio.high: -5,
    Prio.normal: +0,
    Prio.low: +10,
}
if has_win32process:
    if hasattr(win32process, "BELOW_NORMAL_PRIORITY_CLASS"):
        low = win32process.BELOW_NORMAL_PRIORITY_CLASS
    else:
        low = win32process.IDLE_PRIORITY_CLASS
    if hasattr(win32process, "ABOVE_NORMAL_PRIORITY_CLASS"):
        high = win32process.ABOVE_NORMAL_PRIORITY_CLASS
    else:
        high = win32process.HIGH_PRIORITY_CLASS
    _nt_prio_val = {
        Prio.high: high,
        Prio.normal: win32process.NORMAL_PRIORITY_CLASS,
        Prio.low: low,
    }
    del low, high


def set_thread_priority (prio):
    """Set priority of this thread (and thus also for all spawned threads)."""
    if os.name == 'nt' and has_win32process:
        res = win32process.SetPriorityClass(
                   win32process.GetCurrentProcess(), _nt_prio_val[prio])
    elif os.name == 'posix':
        res = os.nice(_posix_nice_val[prio])
    else:
        res = None
    return res


class StoppableThread (threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__ (self):
        """Store stop event."""
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop (self):
        """Set stop event."""
        self._stop.set()

    def stopped (self):
        """Return True if stop event is set."""
        return self._stop.isSet()
