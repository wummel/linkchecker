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
        self.addAction(parent.actionCopyToClipboard)
        self.addAction(parent.actionViewParentOnline)
        self.addAction(parent.actionViewParentSource)

    def enableFromItem (self, item):
        """Enable context menu actions depending on the item content."""
        parent = self.parentWidget()
        data = item.url_data
        # enable view online actions
        parent.actionViewOnline.setEnabled(bool(data.url))
        parent.actionViewParentOnline.setEnabled(bool(data.parent_url))
        # enable view source actions
        enable_parent_url_source = self.can_view_source(data.parent_url)
        parent.actionViewParentSource.setEnabled(enable_parent_url_source)

    def can_view_source (self, url, result=None):
        """Determine if URL source could be retrieved."""
        if not url:
            return False
        if result and result.startswith(u"Error"):
            return False
        return (url.startswith(u"http:") or
                url.startswith(u"https:") or
                url.startswith(u"ftp:") or
                url.startswith(u"ftps:") or
                url.startswith(u"file:"))
