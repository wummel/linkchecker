# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2007 Bastian Kleineidam
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
import thread
import linkcheck.decorators
import linkcheck.log
import linkcheck.threader
import console


class CheckedTask (linkcheck.threader.StoppableThread):
    """Stoppable URL check task, handling error conditions while running."""

    def run (self):
        """Handle keyboard interrupt and other errors."""
        try:
            self.run_checked()
        except KeyboardInterrupt:
            linkcheck.log.warn(linkcheck.LOG_CHECK,
                "interrupt did not reach the main thread")
            thread.interrupt_main()
        except:
            console.internal_error()

    @linkcheck.decorators.notimplemented
    def run_checked (self):
        """Overload in subclass."""
        pass
