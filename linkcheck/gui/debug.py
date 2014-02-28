# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2014 Bastian Kleineidam
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
from .linkchecker_ui_debug import Ui_DebugDialog


class LinkCheckerDebug (QtGui.QDialog, Ui_DebugDialog):
    """Show debug text."""

    log_msg_signal = QtCore.pyqtSignal(str)

    def __init__ (self, parent=None):
        """Setup the debug message dialog."""
        super(LinkCheckerDebug, self).__init__(parent)
        self.setupUi(self)
        font = QtGui.QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.textEdit.document().setDefaultFont(font)
        self.log_msg_signal.connect(self.textEdit.appendPlainText)
        self.reset()

    def reset (self):
        """Clear all debug info."""
        self.textEdit.clear()

    def getText (self):
        """Get debug info as string."""
        return self.textEdit.toPlainText()
