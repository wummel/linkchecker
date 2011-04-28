# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2011 Bastian Kleineidam
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
        self.progress = None

    def check (self, aggregate, progress):
        """Set check variables and start the thread."""
        self.aggregate = aggregate
        self.progress = progress
        self.progress.cancelButton.clicked.connect(self.cancel)
        # setup the thread and call run()
        self.start()

    def cancel (self):
        """Reset check variables and set stop flag."""
        if self.progress is not None:
            self.progress = None
        if self.aggregate is not None:
            self.aggregate.cancel()
            self.aggregate = None

    def run (self):
        """Start checking."""
        assert self.aggregate.config["threads"] > 0
        director.check_urls(self.aggregate)
