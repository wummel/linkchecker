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
from PyQt4 import QtGui

class ContextMenu (QtGui.QMenu):
    """Show context menu."""

    def __init__ (self, parent=None):
        super(ContextMenu, self).__init__(parent)
        self.addAction(parent.actionViewOnline)
        self.addAction(parent.actionViewSource)
        self.addAction(parent.actionCopyToClipboard)
        self.addAction(parent.actionViewParentOnline)

    def enableFromItem (self, item):
        """Enable context menu items dependet on the item content."""
        parent = self.parentWidget()
        has_parenturl = bool(str(item.text(1)))
        parent.actionViewParentOnline.setEnabled(has_parenturl)
        has_url = bool(str(item.text(2)))
        parent.actionViewOnline.setEnabled(has_url)
        parent.actionViewSource.setEnabled(has_url)
