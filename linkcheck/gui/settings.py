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

    def __init__ (self, base, appname):
        self.settings = QtCore.QSettings(base, appname)

    def read_geometry (self):
        self.settings.beginGroup('mainwindow')
        size = pos = None
        if self.settings.contains('size'):
            size = save_size(self.settings.value('size').toSize())
        if self.settings.contains('pos'):
            pos = save_point(self.settings.value('pos').toPoint())
        self.settings.endGroup()
        return size, pos


    def save_geometry (self, size, pos):
        self.settings.beginGroup('mainwindow')
        self.settings.setValue("size", QtCore.QVariant(save_size(size)))
        self.settings.setValue("pos", QtCore.QVariant(save_point(pos)))
        self.settings.endGroup()

    def sync (self):
        self.settings.sync()
