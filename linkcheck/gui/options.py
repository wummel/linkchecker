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

import os
from PyQt4 import QtGui
from .linkchecker_ui_options import Ui_Options
from .editor import EditorWindow
from .. import configuration


class LinkCheckerOptions (QtGui.QDialog, Ui_Options):
    """Hold options for current URL to check."""

    def __init__ (self, parent=None):
        super(LinkCheckerOptions, self).__init__(parent)
        self.setupUi(self)
        self.editor = EditorWindow(self)
        self.closeButton.clicked.connect(self.close)
        self.resetButton.clicked.connect(self.reset)
        self.sys_config_button.clicked.connect(self.edit_sys_config)
        self.user_config_button.clicked.connect(self.edit_user_config)
        self.reset()

    def reset (self):
        """Reset GUI and config options."""
        config = configuration.Configuration()
        files = configuration.get_standard_config_files()
        self.sys_config, self.user_config = files
        config.read(files)
        self.reset_gui_options(config)
        self.reset_config_options()

    def reset_gui_options (self, config):
        """Reset GUI options to default values from config."""
        self.recursionlevel.setValue(config["recursionlevel"])
        self.verbose.setChecked(config["verbose"])
        self.debug.setChecked(False)
        del config

    def reset_config_options (self):
        """Reset configuration file edit buttons."""
        self.sys_config_writable = os.access(self.sys_config, os.W_OK)
        self.user_config_writable = os.access(self.user_config, os.W_OK)
        set_edit_button(self.sys_config, self.sys_config_button,
                        self.sys_config_writable)
        set_edit_button(self.user_config, self.user_config_button,
                        self.user_config_writable)

    def edit_sys_config (self):
        return start_editor(self.sys_config, self.sys_config_writable,
                            self.editor)

    def edit_user_config (self):
        return start_editor(self.user_config, self.user_config_writable,
                            self.editor)

    def get_options (self):
        """Return option data as dictionary."""
        return dict(
            debug=self.debug.isChecked(),
            verbose=self.verbose.isChecked(),
            recursionlevel=self.recursionlevel.value(),
        )

    def set_options (self, data):
        if data["debug"] is not None:
            self.debug.setChecked(data["debug"])
        if data["verbose"] is not None:
            self.verbose.setChecked(data["verbose"])
        if data["recursionlevel"] is not None:
            self.recursionlevel.setValue(data["recursionlevel"])


def start_editor (filename, writable, editor):
    if not os.path.isfile(filename):
        # file vanished
        return
    editor.load(filename)
    editor.setContentType("text/plain+ini")
    editor.editor.setReadOnly(not writable)
    editor.show()


def set_edit_button (filename, button, writable):
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
