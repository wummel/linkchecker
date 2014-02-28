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

from PyQt4 import QtCore, QtGui
from .. import updater, configuration


class UpdateThread (QtCore.QThread):
    """Thread to check for updated versions."""

    def reset (self):
        """Reset version information."""
        self.result = self.value = None

    def run (self):
        """Check for updated version."""
        self.result, self.value = updater.check_update()


class UpdateDialog (QtGui.QMessageBox):
    """Dialog displaying results of an update check."""

    def __init__ (self, parent=None):
        """Initialize dialog and start background update thread."""
        super(UpdateDialog, self).__init__(parent)
        title = _('%(app)s update information') % dict(app=configuration.App)
        self.setWindowTitle(title)
        self.thread = UpdateThread()
        self.thread.finished.connect(self.update)

    def reset (self):
        """Reset dialog and restart update check."""
        self.thread.reset()
        self.thread.start()
        self.setIcon(QtGui.QMessageBox.Information)
        self.setText(_('Checking for updates...'))

    def update (self):
        """Display update thread result (which must be available)."""
        result, value = self.thread.result, self.thread.value
        if result:
            if value is None:
                # no update available: display info
                text = _('Congratulations: the latest version '
                         '%(app)s is installed.')
                attrs = dict(app=configuration.App)
            else:
                version, url = value
                if url is None:
                    # current version is newer than online version
                    text = _('Detected local or development version %(currentversion)s. '
                             'Available version of %(app)s is %(version)s.')
                else:
                    # display update link
                    text = _('A new version %(version)s of %(app)s is '
                             'available for <a href="%(url)s">download</a>.')
                attrs = dict(version=version, app=configuration.AppName,
                             url=url, currentversion=configuration.Version)
        else:
            # value is an error message or None if UpdateThread has been
            # terminated
            if value is None:
                value = _('update thread has been terminated')
            self.setIcon(QtGui.QMessageBox.Warning)
            text = _('An error occured while checking for an '
                     'update of %(app)s: %(error)s.')
            attrs = dict(error=value, app=configuration.AppName)
        self.setText(text % attrs)
