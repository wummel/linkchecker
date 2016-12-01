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
try: # Python 3
    import _thread
except ImportError: # Python 2
    import thread as _thread
from ..decorators import notimplemented
from .. import threader
from . import console


class CheckedTask (threader.StoppableThread):
    """Stoppable URL check task, handling error conditions while running."""

    def run (self):
        """Handle keyboard interrupt and other errors."""
        try:
            self.run_checked()
        except KeyboardInterrupt:
            _thread.interrupt_main()
        except Exception:
            self.internal_error()

    @notimplemented
    def run_checked (self):
        """Overload in subclass."""
        pass

    @notimplemented
    def internal_error (self):
        """Overload in subclass."""
        pass


class LoggedCheckedTask (CheckedTask):
    """URL check task with a logger instance and internal error handling."""

    def __init__ (self, logger):
        """Initialize super instance and store given logger."""
        super(CheckedTask, self).__init__()
        self.logger = logger

    def internal_error (self):
        """Log an internal error on console and the logger."""
        console.internal_error()
        self.logger.log_internal_error()
