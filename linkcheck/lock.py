# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2006 Bastian Kleineidam
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

import linkcheck
import linkcheck.log

lock_klass = threading.RLock().__class__

class AssertLock (lock_klass):
    """
    Lock class asserting that only available locks are acquired,
    and that no lock is released twice.
    """

    def acquire (self, blocking=True):
        """
        Acquire lock.
        """
        assert not self.is_locked(), "deadlock"
        assert None == linkcheck.log.debug(linkcheck.LOG_THREAD,
            "Acquire %s", self)
        super(AssertLock, self).acquire(blocking=blocking)

    def release (self):
        """
        Release lock.
        """
        assert self.is_locked(), "double release"
        assert None == linkcheck.log.debug(linkcheck.LOG_THREAD,
            "Release %s", self)
        super(AssertLock, self).release()

    def is_locked (self):
        """
        See if this lock is owned.
        """
        return self._is_owned()
