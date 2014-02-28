# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2014 Bastian Kleineidam
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

import os
from PyQt4 import QtGui
from .linkchecker_ui_options import Ui_Options
from .editor import EditorWindow
from ..fileutil import is_writable
from .. import configuration


class LinkCheckerOptions (QtGui.QDialog, Ui_Options):
    """Hold options for current URL to check."""

    def __init__ (self, parent=None):
        """Reset all options and initialize the editor window."""
        super(LinkCheckerOptions, self).__init__(parent)
        self.setupUi(self)
        self.editor = EditorWindow(self)
        self.closeButton.clicked.connect(self.close)
        self.user_config_button.clicked.connect(self.edit_user_config)
        self.reset()

    def reset (self):
        """Reset GUI and config options."""
        self.user_config = configuration.get_user_config()
        self.reset_gui_options()
        self.reset_config_options()

    def reset_gui_options (self):
        """Reset GUI options to default values."""
        self.recursionlevel.setValue(-1)
        self.verbose.setChecked(False)
        self.debug.setChecked(False)
        self.warninglines.setPlainText(u"")
        self.ignorelines.setPlainText(u"")

    def reset_config_options (self):
        """Reset configuration file edit buttons."""
        self.user_config_writable = is_writable(self.user_config)
        set_edit_button(self.user_config, self.user_config_button,
                        self.user_config_filename, self.user_config_writable)

    def edit_user_config (self):
        """Show editor for user specific configuration file."""
        return start_editor(self.user_config, self.user_config_writable,
                            self.editor)

    def get_options (self):
        """Return option data as dictionary."""
        return dict(
            debug=self.debug.isChecked(),
            verbose=self.verbose.isChecked(),
            recursionlevel=self.recursionlevel.value(),
            warninglines=unicode(self.warninglines.toPlainText()),
            ignorelines=unicode(self.ignorelines.toPlainText()),
        )

    def set_options (self, data):
        """Set GUI options from given data."""
        if data.get("debug") is not None:
            self.debug.setChecked(data["debug"])
        if data.get("verbose") is not None:
            self.verbose.setChecked(data["verbose"])
        if data.get("recursionlevel") is not None:
            self.recursionlevel.setValue(data["recursionlevel"])
        if data.get("warninglines") is not None:
            self.warninglines.setPlainText(data["warninglines"])
        if data.get("ignorelines") is not None:
            self.ignorelines.setPlainText(data["ignorelines"])


def start_editor (filename, writable, editor):
    """Start editor for given filename."""
    if not os.path.isfile(filename):
        # file vanished
        return
    editor.load(filename)
    # all config files are in INI format
    editor.setContentType("text/plain+ini")
    editor.editor.setReadOnly(not writable)
    editor.show()


def set_edit_button (filename, button, label, writable):
    """Update edit button depending on writable flag of file."""
    label.setText(filename)
    if os.path.isfile(filename):
        button.setEnabled(True)
        if writable:
            button.setText(_(u"Edit"))
        else:
            button.setText(_(u"Read"))
    else:
        button.setEnabled(False)
        button.setText(_(u"File not found"))
