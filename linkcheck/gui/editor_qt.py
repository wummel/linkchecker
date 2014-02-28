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
Text editor implemented with Qt
"""
from PyQt4 import QtGui, QtCore
from . import syntax

# Map MIME type to QSyntaxHighlighter class
ContentTypeLexers = {
    "text/html": syntax.HtmlHighlighter,
    "application/xml": syntax.XmlHighlighter,
    "text/plain+ini": syntax.IniHighlighter,
}

class LineNumberArea (QtGui.QWidget):
    """Display line numbers."""

    def sizeHint (self):
        """Return calculated width for line number area."""
        return QtCore.QSize(self.parentWidget().lineNumberAreaWidth(), 0)

    def paintEvent (self, event):
        """Call paint method of parent widget."""
        self.parentWidget().lineNumberAreaPaintEvent(event)


class Editor (QtGui.QPlainTextEdit):
    """Qt editor with line numbering."""

    def __init__ (self, parent):
        """Initialize line numbering."""
        super(Editor, self).__init__(parent)
        font = QtGui.QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.document().setDefaultFont(font)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def highlight (self, lexerclass):
        """Set syntax highlighter."""
        if lexerclass:
            self.lexer = lexerclass(self.document())
        else:
            self.lexer = None

    def setText (self, text):
        """Set editor text."""
        return self.setPlainText(text)

    def text (self):
        """Return editor text."""
        return self.toPlainText()

    def setModified (self, flag):
        """Set modified flag of underlying document."""
        return self.document().setModified(flag)

    def isModified (self):
        """Return modified flag of underlying document."""
        return self.document().isModified()

    def setCursorPosition (self, line, column=0):
        """Move cursor to given line and column. Line counting starts
        with zero."""
        block = self.document().findBlockByNumber(line)
        if block.isValid():
            cursor = QtGui.QTextCursor(block)
            if column > 0:
                cursor.movePosition(QtGui.QTextCursor.Right,
                                    QtGui.QTextCursor.MoveAnchor, column)
            self.setTextCursor(cursor)
            self.centerCursor()

    def lineNumberAreaPaintEvent (self, event):
        """Paint line numbers."""
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top =  self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QtCore.Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(),
                                 self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def lineNumberAreaWidth (self):
        """Calculate line number area width."""
        digits = max(1, len(str(self.blockCount())))
        onecharwidth = self.fontMetrics().width('9')
        space = 3 + onecharwidth * digits
        return space

    def resizeEvent (self, event):
        """Resize line number area together with editor."""
        super(Editor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                  self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth (self, newBlockCount):
        """Update the line number area width."""
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine (self):
        """Highlight the current line."""
        extraSelections = []
        if not self.isReadOnly():
            selection = QtGui.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(QtCore.Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def updateLineNumberArea (self, rect, dy):
        """Update the line number area."""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(),
                self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
