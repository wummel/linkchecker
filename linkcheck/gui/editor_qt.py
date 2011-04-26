# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Bastian Kleineidam
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

ContentTypeLexers = {}

class LineNumberArea (QtGui.QWidget):
    def __init__ (self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor

    def sizeHint (self):
        return QtGui.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent (self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class Editor (QtGui.QPlainTextEdit):

    def __init__ (self, parent):
        super(Editor, self).__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        #connect(this, SIGNAL(blockCountChanged(int)), this, SLOT(updateLineNumberAreaWidth(int)));
        #connect(this, SIGNAL(updateRequest(QRect,int)), this, SLOT(updateLineNumberArea(QRect,int)));
        #connect(this, SIGNAL(cursorPositionChanged()), this, SLOT(highlightCurrentLine()));
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def setLexer (self):
        pass

    def setText (self, text):
        return self.setPlainText(text)

    def text (self):
        return self.toPlainText()

    def setModified (self, flag):
        return self.document().setModified(flag)

    def isModified (self):
        return self.document().isModified()

    def setCursorPosition (self, line, column=0):
        block = self.document().findBlockByNumber(line)
        if block.isValid():
            cursor = QtGui.QTextCursor(block)
            if column > 0:
                cursor.movePosition(QtGui.QTextCursor.Right,
                                    QtGui.QTextCursor.MoveAnchor, column)
            self.setTextCursor(cursor)
            self.centerCursor()

    def lineNumberAreaPaintEvent (self, event):
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
        digits = max(1, len(str(self.blockCount())))
        onecharwidth = self.fontMetrics().width('9')
        space = 3 + onecharwidth * digits
        return space

    def resizeEvent (self, event):
        super(Editor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                  self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth (self, newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine (self):
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
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(),
                self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
