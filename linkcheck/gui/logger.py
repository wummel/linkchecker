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

from PyQt4 import QtCore
from logging import Handler
from ..logger import Logger


class GuiLogHandler (Handler, object):
    """Delegate log messages to the UI."""

    def __init__ (self, widget):
        """Save widget."""
        super(GuiLogHandler, self).__init__()
        self.widget = widget

    def emit (self, record):
        """Emit a record. It gets logged in the progress window."""
        msg = self.format(record)
        self.widget.emit(QtCore.SIGNAL("log_msg(QString)"), msg)


class GuiLogger (Logger):
    """Delegate log URLs to the UI tree widget."""

    def __init__ (self, **args):
        super(GuiLogger, self).__init__(**args)
        self.widget = args["widget"]

    def start_fileoutput (self):
        pass

    def close_fileoutput (self):
        pass

    def log_url (self, url_data):
        """URL gets logged in the main window."""
        self.widget.emit(QtCore.SIGNAL("log_url(PyQt_PyObject)"), url_data)

    def end_output (self):
        pass

    def start_output (self):
        pass
