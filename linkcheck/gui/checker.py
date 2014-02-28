# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2014 Bastian Kleineidam
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
from PyQt4 import QtCore
from .. import director


class CheckerThread (QtCore.QThread):
    """Separate checker thread."""

    def __init__ (self, parent=None):
        """Reset check variables."""
        super(CheckerThread, self).__init__(parent)
        self.aggregate = None

    def check (self, aggregate):
        """Set check variables and start the thread."""
        self.aggregate = aggregate
        # setup the thread and call run()
        self.start()

    def cancel (self):
        """Reset check variables and set stop flag."""
        if self.aggregate is not None:
            aggregate = self.aggregate
            self.aggregate = None
            aggregate.cancel()

    def run (self):
        """Start checking."""
        assert self.aggregate.config["threads"] > 0
        director.check_urls(self.aggregate)
