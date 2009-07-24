# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2009 Bastian Kleineidam
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
        super(CheckerThread, self).__init__(parent)
        self.exiting = False
        self.aggregate = None
        self.progress = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def check (self, aggregate, progress):
        self.aggregate = aggregate
        self.progress = progress
        self.connect(self.progress.cancelButton, QtCore.SIGNAL("clicked()"), self.cancel)
        # setup the thread and call run()
        self.start()

    def cancel (self):
        # stop checking
        if self.progress is not None:
            self.progress.cancelButton.setEnabled(False)
            self.progress = None
        if self.aggregate is not None:
            self.aggregate.wanted_stop = True
            self.aggregate = None

    def run (self):
        # start checking
        director.check_urls(self.aggregate)
