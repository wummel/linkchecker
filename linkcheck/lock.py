# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005  Bastian Kleineidam
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
Locking utility class.
"""

try:
    import threading
except ImportError:
    import dummy_threading as threading

lock_klass = threading.RLock().__class__

class AssertLock (lock_klass):

    def acquire (self, blocking=True):
        """
        Acquire lock.
        """
        assert not self._is_owned(), "deadlock"
        super(AssertLock, self).acquire(blocking=blocking)

    def release (self):
        """
        Release lock.
        """
        assert self._is_owned(), "double release"
        super(AssertLock, self).release()

