# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010 Bastian Kleineidam
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
from .. import strformat


Headers = [u"#", _(u"Parent"), _(u"URL"), _(u"Name"), _(u"Result")]
EmptyHeader = QtCore.QVariant()

class UrlItem (object):
    """URL item model storing info to be displayed."""

    def __init__ (self, url_data, number):
        # store plain data
        self.id = number
        self.url = url_data.url
        self.base_url = url_data.base_url
        self.name = url_data.name
        self.parent_url = url_data.parent_url
        self.base_ref = url_data.base_ref
        self.dltime = url_data.dltime
        self.dlsize = url_data.dlsize
        self.checktime = url_data.checktime
        self.info = url_data.info[:]
        self.warnings = url_data.warnings[:]
        self.valid = url_data.value
        self.result = url_data.result
        self.line = url_data.line
        self.column = url_data.column
        # format display and tooltips
        self.init_display()
        self.init_tooltips()

    def init_display (self):
        # Parent URL
        if self.parent_url:
            parent = unicode(self.parent_url) + \
                (_(", line %d") % self.line) + \
                (_(", col %d") % self.column)
        else:
            parent = u""
        # Result
        if self.valid:
            if self.warnings:
                self.color = QtCore.Qt.darkYellow
            else:
                self.color = QtCore.Qt.darkGreen
            result = u"Valid"
        else:
            self.color = QtCore.Qt.darkRed
            result = u"Error"
        if self.result:
            result += u": %s" % self.result
        self.display.append(result)
        self.display = [
            # ID
            u"%09d" % self.number,
            # Parent URL
            parent,
            # URL
            unicode(self.url),
            # Name
            self.name,
            # Result
            result,
        ]

    def init_tooltips (self):
        # Result
        if self.warnings:
            result = strformat.wrap(u"\n".join(self.warnings), 60)
        else:
            result = u""
        self.tooltips = [
            # ID
            u"",
            # Parent URL
            u"",
            # URL
            unicode(self.url),
            # Name
            self.name,
            # Result
            result,
        ]


class UrlItemModel(QtCore.QAbstractItemModel):

    def __init__ (self, parent=None):
        super(UrlItemModel, self).__init__(parent)
        # list of UrlItem objects
        self.urls = []

    def rowCount (self, parent=QtCore.QModelIndex()):
        return len(self.urls)

    def columnCount (self, parent=QtCore.QModelIndex()):
        return len(Headers)

    def parent (self, child=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    def index (self, row, column, parent=QtCore.QModelIndex()):
        return self.createIndex(row, column)

    def data (self, index, role=QtCore.Qt.DisplayRole):
        V = QtCore.QVariant
        if not index.isValid or \
           not (0 <= index.row() < len(self.urls)):
            return V()
        urlitem = self.data[index.row()]
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            return V(urlitem.display[column])
        elif role == QtCore.Qt.ToolTipRole:
            return V(urlitem.tooltips[column])
        elif role == QtCore.Qt.TextColorRole and column == 4:
            return V(urlitem.color)
        else:
            return V()

    def headerData (self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
           role == QtCore.Qt.DisplayRole:
            return Headers[section]
        return EmptyHeader

    def flags (self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def clear (self):
        self.beginResetModel()
        self.urls = []
        self.endResetModel()

    def addUrlItem (self, urlitem):
        self.urls.append(urlitem)
        return self.insertRows(self.rowCount())
