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

import os
import urlparse
from PyQt4 import QtGui, QtCore
from .linkchecker_ui_editor import Ui_EditorDialog
from ..checker.fileurl import get_os_filename
try:
    from .editor_qsci import ContentTypeLexers, Editor
except ImportError:
    from .editor_qt import ContentTypeLexers, Editor

class EditorWindow (QtGui.QDialog, Ui_EditorDialog):
    """Editor window."""

    # emitted after successful save
    saved = QtCore.pyqtSignal(str)
    # emitted after successful load
    loaded = QtCore.pyqtSignal(str)

    def __init__ (self, parent=None):
        """Initialize the editor widget."""
        super(EditorWindow, self).__init__(parent)
        self.setupUi(self)
        # filename used for saving
        self.filename = None
        # the Scintilla editor widget
        self.editor = Editor(parent=self.frame)
        layout = QtGui.QVBoxLayout(self.frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        # for debugging
        #self.setText(("1234567890"*8) + "\n<html><head>\n<title>x</title>\n</head>\n")
        #lexer = Qsci.QsciLexerHTML()
        #lexer.setFont(self.editor.font())
        #self.editor.setLexer(lexer)
        #self.editor.setCursorPosition(1, 1)
        #self.show()

    def setContentType (self, content_type):
        """Choose a lexer according to given content type."""
        lexerclass = ContentTypeLexers.get(content_type.lower())
        self.editor.highlight(lexerclass)

    def setText (self, text, line=1, col=1):
        """Set editor text and jump to given line and column."""
        self.editor.setText(text)
        self.editor.setCursorPosition(line-1, col-1)
        self.editor.setModified(False)

    def setUrl (self, url):
        """If URL is a file:// URL, store the filename of it as base
        directory for the "save as" dialog."""
        self.basedir = ""
        if url and url.startswith("file://"):
            urlparts = urlparse.urlsplit(url)
            path = get_os_filename(urlparts[2])
            if os.path.exists(path):
                self.basedir = path

    @QtCore.pyqtSlot()
    def on_actionSave_triggered (self):
        """Save changed editor contents."""
        if self.editor.isModified() or not self.filename:
            self.save()

    def closeEvent (self, e=None):
        """Save settings and remove registered logging handler"""
        if self.editor.isModified():
            # ask if user wants to save
            if self.wants_save():
                if self.save():
                    e.accept()
                else:
                    # saving error or user canceled
                    e.ignore()
            else:
                # discard changes
                e.accept()
        else:
            # unchanged
            e.accept()

    def wants_save (self):
        """Ask user if he wants to save changes. Return True if user
        wants to save, else False."""
        dialog = QtGui.QMessageBox(parent=self)
        dialog.setIcon(QtGui.QMessageBox.Question)
        dialog.setWindowTitle(_("Save file?"))
        dialog.setText(_("The document has been modified."))
        dialog.setInformativeText(_("Do you want to save your changes?"))
        dialog.setStandardButtons(QtGui.QMessageBox.Save |
                                  QtGui.QMessageBox.Discard)
        dialog.setDefaultButton(QtGui.QMessageBox.Save)
        return dialog.exec_() == QtGui.QMessageBox.Save

    def save (self):
        """Save editor contents to file."""
        if not self.filename:
            title = _("Save File As")
            res = QtGui.QFileDialog.getSaveFileName(self, title, self.basedir)
            if not res:
                # user canceled
                return
            self.filename = res
            self.setWindowTitle(self.filename)
        else:
            if not os.path.isfile(self.filename):
                return
            if not os.access(self.filename, os.W_OK):
                return
        fh = None
        saved = False
        try:
            try:
                fh = QtCore.QFile(self.filename)
                if not fh.open(QtCore.QIODevice.WriteOnly):
                    raise IOError(fh.errorString())
                stream = QtCore.QTextStream(fh)
                stream.setCodec("UTF-8")
                stream << self.editor.text()
                self.editor.setModified(False)
                saved = True
            except (IOError, OSError) as e:
                err = QtGui.QMessageBox(self)
                err.setText(str(e))
                err.exec_()
        finally:
            if fh is not None:
                fh.close()
        if saved:
            self.saved.emit(self.filename)
        return saved

    def load (self, filename):
        """Load editor contents from file."""
        if not os.path.isfile(filename):
            return
        if not os.access(filename, os.R_OK):
            return
        self.filename = filename
        if not os.access(filename, os.W_OK):
            title = u"%s (%s)" % (self.filename, _(u"readonly"))
        else:
            title = self.filename
        self.setWindowTitle(title)
        fh = None
        loaded = False
        try:
            try:
                fh = QtCore.QFile(self.filename)
                if not fh.open(QtCore.QIODevice.ReadOnly):
                    raise IOError(fh.errorString())
                stream = QtCore.QTextStream(fh)
                stream.setCodec("UTF-8")
                self.setText(stream.readAll())
                loaded = True
            except (IOError, OSError) as e:
                err = QtGui.QMessageBox(self)
                err.setText(str(e))
                err.exec_()
        finally:
            if fh is not None:
                fh.close()
        if loaded:
            self.loaded.emit(self.filename)
