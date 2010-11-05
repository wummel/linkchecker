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

import os
from PyQt4 import Qsci, QtGui, QtCore
from .linkchecker_ui_editor import Ui_EditorDialog


ContentTypeLexers = {
    "application/x-shellscript": Qsci.QsciLexerBash,
    "application/x-sh": Qsci.QsciLexerBash,
    "application/x-msdos-program": Qsci.QsciLexerBatch,
    #"": Qsci.QsciLexerCMake,
    "text/x-c++src": Qsci.QsciLexerCPP,
    "text/css": Qsci.QsciLexerCSS,
    #"": Qsci.QsciLexerCSharp,
    #"": Qsci.QsciLexerCustom,
    "text/x-dsrc": Qsci.QsciLexerD,
    "text/x-diff": Qsci.QsciLexerDiff,
    #"": Qsci.QsciLexerFortran,
    #"": Qsci.QsciLexerFortran77,
    "text/html": Qsci.QsciLexerHTML,
    #"": Qsci.QsciLexerIDL,
    "text/x-java": Qsci.QsciLexerJava,
    "application/javascript": Qsci.QsciLexerJavaScript,
    #"": Qsci.QsciLexerLua,
    "text/x-makefile": Qsci.QsciLexerMakefile,
    #"": Qsci.QsciLexerPOV,
    "text/x-pascal": Qsci.QsciLexerPascal,
    "text/x-perl": Qsci.QsciLexerPerl,
    "application/postscript": Qsci.QsciLexerPostScript,
    "text/plain+ini": Qsci.QsciLexerProperties,
    "text/x-python": Qsci.QsciLexerPython,
    "application/x-ruby": Qsci.QsciLexerRuby,
    #"": Qsci.QsciLexerSQL,
    #"": Qsci.QsciLexerSpice,
    "application/x-tcl": Qsci.QsciLexerTCL,
    "application/x-latex": Qsci.QsciLexerTeX,
    #"": Qsci.QsciLexerVHDL,
    #"": Qsci.QsciLexerVerilog,
    "application/xml": Qsci.QsciLexerXML,
    #"": Qsci.QsciLexerYAML,
}

class Editor (Qsci.QsciScintilla):

    def __init__ (self, parent=None):
        super(Editor, self).__init__(parent)
        # Use Courier font with fixed width
        font = QtGui.QFont("Consolas", 11)
        font.setFixedPitch(True)

        # Set the default font of the editor
        # and take the same font for line numbers
        self.setFont(font)
        self.setMarginsFont(font)

        # line number margin for 4 digits (plus 2px extra space)
        margin = QtGui.QFontMetrics(font).width("0"*4)+2
        # Display line numbers, margin 0 is for line numbers
        self.setMarginWidth(0, margin)
        self.setMarginLineNumbers(0, True)

        # Show whitespace to help detect whitespace errors
        self.setWhitespaceVisibility(True)

        # Use boxes as folding visual
        self.setFolding(self.BoxedTreeFoldStyle)

        # Braces matching
        self.setBraceMatching(self.SloppyBraceMatch)

        # Editing line color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#e5e5cb"))

        # line numbers margin colors
        self.setMarginsBackgroundColor(QtGui.QColor("#e5e5e5"))
        self.setMarginsForegroundColor(QtGui.QColor("#333333"))

        # folding margin colors (foreground,background)
        self.setFoldMarginColors(QtGui.QColor("#f5f5dc"),QtGui.QColor("#aaaaaa"))


class EditorWindow (QtGui.QDialog, Ui_EditorDialog):

    def __init__ (self, parent=None):
        super(EditorWindow, self).__init__(parent)
        self.setupUi(self)
        # filename used for saving
        self.filename = None
        # the Scintilla editor widget
        self.editor = Editor(parent=self.frame)
        layout = QtGui.QVBoxLayout(self.frame)
        layout.setMargin(0)
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
        if lexerclass:
            lexer = lexerclass()
            lexer.setFont(self.editor.font())
            self.editor.setLexer(lexer)
        else:
            # use no styling
            self.editor.setLexer()

    def setText (self, text, line=1, col=1):
        self.editor.setText(text)
        self.editor.setCursorPosition(line-1, col-1)
        self.editor.setModified(False)

    @QtCore.pyqtSignature("")
    def on_actionSave_triggered (self):
        """Save editor contents."""
        if self.editor.isModified() or not self.filename:
            self.save()

    def save (self):
        if not self.filename:
            res = QtGui.QFileDialog.getSaveFileName(self, "Save File As")
            if not res:
                return
            self.filename = res
            self.setWindowTitle(self.filename)
        if not os.path.isfile(self.filename):
            return
        if not os.access(self.filename, os.W_OK):
            return
        fh = None
        try:
            try:
                fh = QtCore.QFile(self.filename)
                if not fh.open(QtCore.QIODevice.WriteOnly):
                    raise IOError(fh.errorString())
                stream = QtCore.QTextStream(fh)
                stream.setCodec("UTF-8")
                stream << self.editor.text()
                self.editor.setModified(False)
            except (IOError, OSError), e:
                err = QtGui.QMessageBox(self)
                err.setText(str(e))
                err.exec_()
        finally:
            if fh is not None:
                fh.close()

    def load (self, filename):
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
        try:
            try:
                fh = QtCore.QFile(self.filename)
                if not fh.open(QtCore.QIODevice.ReadOnly):
                    raise IOError(fh.errorString())
                stream = QtCore.QTextStream(fh)
                stream.setCodec("UTF-8")
                self.setText(stream.readAll())
            except (IOError, OSError), e:
                err = QtGui.QMessageBox(self)
                err.setText(str(e))
                err.exec_()
        finally:
            if fh is not None:
                fh.close()
