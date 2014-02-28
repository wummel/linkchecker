# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
import operator
from PyQt4 import QtCore, QtGui
from .. import strformat


Headers = [_(u"Parent"), _(u"URL"), _(u"Name"), _(u"Result")]
EmptyQVariant = QtCore.QVariant()


class UrlItem (object):
    """URL item storing info to be displayed."""

    def __init__ (self, url_data):
        """Save given URL data and initialize display and tooltip texts."""
        # url_data is of type CompactUrlData
        self.url_data = url_data
        # format display and tooltips
        self.init_display()
        self.init_tooltips()

    def __getitem__ (self, key):
        """Define easy index access (used for sorting):
           0: Parent URL
           1: URL
           2: URL name
           3: Result
        """
        if not isinstance(key, int):
            raise TypeError("invalid index %r" % key)
        if key == 0:
            return (self.url_data.parent_url, self.url_data.line,
                    self.url_data.column)
        elif key == 1:
            return self.url_data.url
        elif key == 2:
            return self.url_data.name
        elif key == 3:
            return (self.url_data.valid, self.url_data.result)
        raise IndexError("invalid index %d" % key)

    def init_display (self):
        """Store formatted display texts from URL data."""
        # result
        if self.url_data.valid:
            if self.url_data.warnings:
                self.result_color = QtCore.Qt.darkYellow
                text = u"\n".join(x[1] for x in self.url_data.warnings)
                result = u"Warning: %s" % strformat.limit(text, length=25)
            else:
                self.result_color = QtCore.Qt.darkGreen
                result = u"Valid"
                if self.url_data.result:
                    result += u": %s" % self.url_data.result
        else:
            self.result_color = QtCore.Qt.darkRed
            result = u"Error"
            if self.url_data.result:
                result += u": %s" % self.url_data.result
        # Parent URL
        if self.url_data.parent_url:
            parent = u"%s%s%s" % (self.url_data.parent_url,
                (_(", line %d") % self.url_data.line),
                (_(", col %d") % self.url_data.column))
        else:
            parent = u""
        # display values
        self.display = [
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
        """Store formatted tooltip texts from URL data."""
        # Display warnings in result tooltip
        if self.url_data.warnings:
            text = u"\n".join(x[1] for x in self.url_data.warnings)
            result = strformat.wrap(text, 60)
        else:
            result = u""
        self.tooltips = [
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
        """Set empty URL item list."""
        super(UrlItemModel, self).__init__(parent)
        # list of UrlItem objects
        self.urls = []

    def rowCount (self, parent=QtCore.QModelIndex()):
        """Return number of URL items."""
        return len(self.urls)

    def columnCount (self, parent=QtCore.QModelIndex()):
        """Return number of header columns."""
        return len(Headers)

    def parent (self, child=QtCore.QModelIndex()):
        """Return empty QModelIndex since the URL list is not hierarchical."""
        return QtCore.QModelIndex()

    def index (self, row, column, parent=QtCore.QModelIndex()):
        """Return index of URL item in given row and column."""
        return self.createIndex(row, column)

    def data (self, index, role=QtCore.Qt.DisplayRole):
        """Return URL item data at given index for given role."""
        V = QtCore.QVariant
        if not index.isValid() or \
           not (0 <= index.row() < len(self.urls)):
            return EmptyQVariant
        urlitem = self.urls[index.row()]
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            return V(urlitem.display[column])
        elif role == QtCore.Qt.ToolTipRole:
            return V(urlitem.tooltips[column])
        elif role == QtCore.Qt.TextColorRole and column == 3:
            return QtGui.QColor(urlitem.result_color)
        else:
            return EmptyQVariant

    def headerData (self, section, orientation, role):
        """Return header column data for given parameters."""
        if orientation == QtCore.Qt.Horizontal and \
           role == QtCore.Qt.DisplayRole:
            return Headers[section]
        return EmptyQVariant

    def flags (self, index):
        """Return flags that given valid item index is enabled and
        selected."""
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def clear (self):
        """Empty the URL item list."""
        self.beginResetModel()
        self.urls = []
        self.endResetModel()

    def log_url (self, url_data):
        """Add URL data to tree model."""
        row = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.urls.append(UrlItem(url_data))
        self.endInsertRows()
        return True

    def getUrlItem (self, index):
        """Get URL item object at given index."""
        if not index.isValid() or \
           not (0 <= index.row() < len(self.urls)):
            return None
        return self.urls[index.row()]

    def sort (self, column, order=QtCore.Qt.AscendingOrder):
        """Sort URL items by given column and order."""
        self.layoutAboutToBeChanged.emit()
        reverse = (order == QtCore.Qt.DescendingOrder)
        self.urls.sort(key=operator.itemgetter(column), reverse=reverse)
        self.layoutChanged.emit()
