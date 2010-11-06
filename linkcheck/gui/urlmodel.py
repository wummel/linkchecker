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

from PyQt4 import QtCore, QtGui
from .. import strformat


Headers = [u"#", _(u"Parent"), _(u"URL"), _(u"Name"), _(u"Result")]
EmptyHeader = QtCore.QVariant()


class UrlItem (object):
    """URL item storing info to be displayed."""

    def __init__ (self, url_data, number):
        self.number = number
        # url_data is of type CompactUrlData
        self.url_data = url_data
        # format display and tooltips
        self.init_display()
        self.init_tooltips()

    def init_display (self):
        # Parent URL
        if self.url_data.parent_url:
            parent = unicode(self.url_data.parent_url) + \
                (_(", line %d") % self.url_data.line) + \
                (_(", col %d") % self.url_data.column)
        else:
            parent = u""
        # Result
        if self.url_data.valid:
            if self.url_data.warnings:
                self.result_color = QtCore.Qt.darkYellow
            else:
                self.result_color = QtCore.Qt.darkGreen
            result = u"Valid"
        else:
            self.result_color = QtCore.Qt.darkRed
            result = u"Error"
        if self.url_data.result:
            result += u": %s" % self.url_data.result
        self.display = [
            # ID
            u"%09d" % self.number,
            # Parent URL
            parent,
            # URL
            unicode(self.url_data.url),
            # Name
            self.url_data.name,
            # Result
            result,
        ]

    def init_tooltips (self):
        # Display warnings in result tooltip
        if self.url_data.warnings:
            result = strformat.wrap(u"\n".join(self.url_data.warnings), 60)
        else:
            result = u""
        self.tooltips = [
            # ID
            u"",
            # Parent URL
            u"",
            # URL
            unicode(self.url_data.url),
            # Name
            self.url_data.name,
            # Result
            result,
        ]


class UrlItemModel(QtCore.QAbstractItemModel):
    """Model class for list of URL items."""

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
        if not index.isValid() or \
           not (0 <= index.row() < len(self.urls)):
            return V()
        urlitem = self.urls[index.row()]
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            return V(urlitem.display[column])
        elif role == QtCore.Qt.ToolTipRole:
            return V(urlitem.tooltips[column])
        elif role == QtCore.Qt.TextColorRole and column == 4:
            return QtGui.QColor(urlitem.result_color)
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
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.urls.append(urlitem)
        self.endInsertRows()
        return True

    def getUrlItem (self, index):
        if not index.isValid() or \
           not (0 <= index.row() < len(self.urls)):
            return None
        return self.urls[index.row()]
