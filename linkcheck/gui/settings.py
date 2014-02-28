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
"""Read and store QSettings for this application."""

from PyQt4 import QtCore


def save_point (qpoint):
    """Ensure positive X and Y values of point."""
    qpoint.setX(max(0, qpoint.x()))
    qpoint.setY(max(0, qpoint.y()))
    return qpoint


def save_size (qsize):
    """Ensure minimum width and height values of the given size."""
    qsize.setWidth(max(400, qsize.width()))
    qsize.setHeight(max(400, qsize.height()))
    return qsize


class Settings (object):
    """Save and read GUI settings."""

    def __init__ (self, base, appname):
        """Initialize a QSettings object."""
        self.settings = QtCore.QSettings(base, appname)

    def read_geometry (self):
        """Return stored size and position of main window."""
        data = dict(size=None, pos=None)
        self.settings.beginGroup('mainwindow')
        if self.settings.contains('size'):
            data["size"] = save_size(self.settings.value('size').toSize())
        if self.settings.contains('pos'):
            data["pos"] = save_point(self.settings.value('pos').toPoint())
        self.settings.endGroup()
        return data

    def save_geometry (self, data):
        """Save size and position of main window."""
        size = save_size(data["size"])
        pos = save_point(data["pos"])
        self.settings.beginGroup('mainwindow')
        self.settings.setValue("size", QtCore.QVariant(size))
        self.settings.setValue("pos", QtCore.QVariant(pos))
        self.settings.endGroup()

    def read_treeviewcols (self):
        """Return widths of URL treeview columns."""
        data = dict(col1=200, col2=200, col3=150)
        self.settings.beginGroup('treeview')
        for key in ("col1", "col2", "col3"):
            if self.settings.contains(key):
                value, ok = self.settings.value(key).toInt()
                if ok:
                    if value < 50:
                        value = 50
                    elif value > 500:
                        value = 500
                    data[key] = value
        self.settings.endGroup()
        return data

    def save_treeviewcols (self, data):
        """Save widths of URL treeview columns."""
        self.settings.beginGroup('treeview')
        for key in ("col1", "col2", "col3"):
            self.settings.setValue(key, QtCore.QVariant(data[key]))
        self.settings.endGroup()

    def read_options (self):
        """Return stored GUI options."""
        data = dict(debug=None, verbose=None,
            recursionlevel=None, warninglines=None, ignorelines=None)
        self.settings.beginGroup('output')
        for key in ("debug", "verbose"):
            if self.settings.contains(key):
                data[key] = self.settings.value(key).toBool()
        self.settings.endGroup()
        self.settings.beginGroup('checking')
        if self.settings.contains('recursionlevel'):
            value, ok = self.settings.value('recursionlevel').toInt()
            if ok:
                if value < -1:
                    value = -1
                elif value > 100:
                    # 100 is the maximum GUI option value
                    value = 100
            else:
                value = -1
            data['recursionlevel'] = value
        if self.settings.contains('warninglines'):
            value = self.settings.value('warninglines').toString()
            data['warninglines'] = unicode(value)
        if self.settings.contains('ignorelines'):
            value = self.settings.value('ignorelines').toString()
            data['ignorelines'] = unicode(value)
        self.settings.endGroup()
        return data

    def save_options (self, data):
        """Save GUI options."""
        self.settings.beginGroup('output')
        for key in ("debug", "verbose"):
            self.settings.setValue(key, QtCore.QVariant(data[key]))
        self.settings.endGroup()
        self.settings.beginGroup('checking')
        for key in ("recursionlevel", "warninglines", "ignorelines"):
            self.settings.setValue(key, QtCore.QVariant(data[key]))
        self.settings.endGroup()

    def read_recent_documents (self):
        """Return list of recent documents."""
        self.settings.beginGroup('recent')
        data = self.settings.value('documents').toStringList()
        self.settings.endGroup()
        return [unicode(doc) for doc in data]

    def save_recent_documents (self, data):
        """Save list of recent documents."""
        self.settings.beginGroup('recent')
        self.settings.setValue('documents', QtCore.QVariant(data))
        self.settings.endGroup()

    def read_misc(self):
        """Get misc options."""
        data = dict(saveresultas=None)
        self.settings.beginGroup('misc')
        key = 'saveresultas'
        value = self.settings.value(key).toString()
        data[key] = unicode(value)
        self.settings.endGroup()
        return data

    def save_misc(self, data):
        """Save misc options."""
        self.settings.beginGroup('misc')
        key = 'saveresultas'
        self.settings.setValue(key, QtCore.QVariant(data[key]))
        self.settings.endGroup()

    def sync (self):
        """Synchronize QSettings object to disk."""
        self.settings.sync()
