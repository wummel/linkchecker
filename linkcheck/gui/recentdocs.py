# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011-2014 Bastian Kleineidam
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

EmptyQVariant = QtCore.QVariant()


class RecentDocumentModel(QtCore.QAbstractListModel):
    """Model class for list of recent documents."""

    def __init__ (self, parent=None, documents=[], maxentries=10):
        """Set document list."""
        super(RecentDocumentModel, self).__init__(parent)
        self.maxentries = maxentries
        self.documents = documents[:maxentries]

    def rowCount (self, parent=QtCore.QModelIndex()):
        """Return number of documents."""
        return len(self.documents)

    def index (self, row, column=0, parent=QtCore.QModelIndex()):
        """Return index of document in given row."""
        return self.createIndex(row, column)

    def data (self, index, role=QtCore.Qt.DisplayRole):
        """Return data at given index for given role."""
        V = QtCore.QVariant
        if not index.isValid() or \
           not (0 <= index.row() < len(self.documents)) or \
           index.column() != 0:
            return EmptyQVariant
        if role == QtCore.Qt.DisplayRole:
            return V(self.documents[index.row()])
        return EmptyQVariant

    def headerData (self, section, orientation, role):
        """Return header column data for given parameters."""
        return EmptyQVariant

    def flags (self, index):
        """Return flags that given valid item index is enabled and
        selected."""
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def clear (self):
        """Empty the document list."""
        self.beginResetModel()
        self.documents = []
        self.endResetModel()

    def add_document (self, document):
        """Add document to model."""
        if not document:
            return False
        assert isinstance(document, unicode)
        while document in self.documents:
            row = self.documents.index(document)
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self.documents[row]
            self.endRemoveRows()
        while len(self.documents) >= self.maxentries:
            row = len(self.documents) - 1
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self.documents[row]
            self.endRemoveRows()
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.documents.insert(0, document)
        self.endInsertRows()
        return True

    def get_documents (self):
        """Return copy of document list."""
        return self.documents[:]
