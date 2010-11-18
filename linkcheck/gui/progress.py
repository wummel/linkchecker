# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2010 Bastian Kleineidam
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

from PyQt4 import QtCore, QtGui
from .linkchecker_ui_progress import Ui_ProgressDialog


class LinkCheckerProgress (QtGui.QDialog, Ui_ProgressDialog):
    """Show progress bar."""

    log_status_signal = QtCore.pyqtSignal(int, int, int, float)

    def __init__ (self, parent=None):
        super(LinkCheckerProgress, self).__init__(parent)
        self.setupUi(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.log_status_signal.connect(self.log_status)
        self.cancelButton.clicked.connect(self.cancel)

    def log_status (self, checked, in_progress, queued, duration):
        self.label_checked.setText(u"%d" % checked)
        self.label_active.setText(u"%d" % in_progress)
        self.label_queued.setText(u"%d" % queued)

    def reset (self):
        self.cancelButton.setEnabled(True)
        self.label_active.setText(u"0")
        self.label_queued.setText(u"0")
        self.label_checked.setText(u"0")
        self.cancelLabel.setText(u"")

    def cancel (self):
        self.cancelButton.setEnabled(False)
        self.cancelLabel.setText(_(u"Closing pending connections..."))


class StatusLogger (object):
    """GUI status logger, printing to progress dialog."""

    def __init__ (self, signal):
        self.signal = signal

    def log_status (self, checked, in_progress, queued, duration):
        self.signal.emit(checked, in_progress, queued, duration)
