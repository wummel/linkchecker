# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2011 Bastian Kleineidam
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
from .validator import PyRegexValidator, check_regex
from .. import configuration


class LinkCheckerOptions (QtGui.QDialog, Ui_Options):
    """Hold options for current URL to check."""

    def __init__ (self, parent=None):
        """Reset all options and initialize the editor window."""
        super(LinkCheckerOptions, self).__init__(parent)
        self.setupUi(self)
        self.validator = PyRegexValidator(self.warningregex)
        self.warningregex.setValidator(self.validator)
        self.warningregex.textChanged.connect(self.check_warningregex)
        self.editor = EditorWindow(self)
        self.closeButton.clicked.connect(self.close)
        self.user_config_button.clicked.connect(self.edit_user_config)
        self.reset()

    def check_warningregex (self, text):
        """Display red text for invalid regex contents."""
        if check_regex(unicode(text)):
            style = "QLineEdit {}"
            self.warningregex.setStyleSheet(style)
            self.warningregex.setToolTip(u"")
        else:
            # red text
            style = "QLineEdit {color:#aa0000;}"
            self.warningregex.setStyleSheet(style)
            self.warningregex.setToolTip(_("Invalid regular expression"))

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
        self.warningregex.setText(u"")

    def reset_config_options (self):
        """Reset configuration file edit buttons."""
        self.user_config_writable = os.access(self.user_config, os.W_OK)
        set_edit_button(self.user_config, self.user_config_button,
                        self.user_config_writable)

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
            warningregex=unicode(self.warningregex.text()),
        )

    def set_options (self, data):
        """Set GUI options from given data."""
        if data["debug"] is not None:
            self.debug.setChecked(data["debug"])
        if data["verbose"] is not None:
            self.verbose.setChecked(data["verbose"])
        if data["recursionlevel"] is not None:
            self.recursionlevel.setValue(data["recursionlevel"])
        if data["warningregex"] is not None:
            self.warningregex.setText(data["warningregex"])


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


def set_edit_button (filename, button, writable):
    """Update edit button depending on writable flag of file."""
    button.setToolTip(filename)
    if os.path.isfile(filename):
        button.setEnabled(True)
        if writable:
            button.setText(_(u"Edit"))
        else:
            button.setText(_(u"Read"))
    else:
        button.setEnabled(False)
        button.setText(_(u"File not found"))
