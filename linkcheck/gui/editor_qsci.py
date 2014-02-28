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
"""
Text editor implemented with QScintilla
"""
from PyQt4 import QtGui, Qsci

# Map MIME type to Scintilla lexer class
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
    """Configured QsciScintilla widget."""

    def __init__ (self, parent=None):
        """Set Scintilla options for font, colors, etc."""
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
        self.setFoldMarginColors(QtGui.QColor("#f5f5dc"),
                                 QtGui.QColor("#aaaaaa"))

    def highlight (self, lexerclass):
        """Set syntax highlighter."""
        if lexerclass:
            lexer = lexerclass()
            lexer.setFont(self.font())
            self.setLexer(lexer)
        else:
            # use no styling
            self.setLexer()
