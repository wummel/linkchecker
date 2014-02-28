# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
"""Status message handling"""
import time
from . import task
from .. import log, LOG_CHECK, strformat


class Interrupt (task.CheckedTask):
    """Thread that raises KeyboardInterrupt after a specified duration.
    This gives us a portable SIGALRM implementation.
    The duration is checked every 5 seconds.
    """
    WaitSeconds = 5

    def __init__ (self, duration):
        """Initialize the task.
        @param duration: raise KeyboardInterrupt after given number of seconds
        @ptype duration: int
        """
        super(Interrupt, self).__init__()
        self.duration = duration

    def run_checked (self):
        """Wait and raise KeyboardInterrupt after."""
        self.start_time = time.time()
        self.setName("Interrupt")
        while not self.stopped(self.WaitSeconds):
            duration = time.time() - self.start_time
            if duration > self.duration:
                log.warn(LOG_CHECK, "Interrupt after %s" % strformat.strduration_long(duration))
                raise KeyboardInterrupt()
