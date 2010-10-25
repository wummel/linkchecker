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
from .linkchecker_ui_debug import Ui_DebugDialog


class LinkCheckerDebug (QtGui.QDialog, Ui_DebugDialog):
    """Show debug text."""

    def __init__ (self, parent=None):
        super(LinkCheckerDebug, self).__init__(parent)
        self.setupUi(self)
        self.connect(self, QtCore.SIGNAL("log_msg(QString)"), self.log_msg)
        self.reset()

    def log_msg (self, msg):
        self.textEdit.appendPlainText(msg)

    def reset (self):
        self.textEdit.clear()
