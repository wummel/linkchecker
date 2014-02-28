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

from PyQt4 import QtCore, QtGui

class LineEdit (QtGui.QLineEdit):
    """A line edit widget displaying a clear button if there is some text
    and a down-arrow button displaying a list of strings (eg. recent
    documents)."""

    def __init__ (self, parent=None):
        """Initialize buttons and size settings."""
        super(LineEdit, self).__init__(parent)
        self.listmodel = None
        self.listview = None
        self.setup_clear_button()
        self.setup_list_button()
        self.setup_size_metrics()

    def setup_clear_button (self):
        """Initialize the clear button."""
        self.clearButton = QtGui.QToolButton(self)
        pixmap = QtGui.QPixmap(":/icons/clear.png")
        self.clearButton.setIcon(QtGui.QIcon(pixmap))
        self.clearButton.setIconSize(pixmap.size())
        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        style = "QToolButton { border: none; padding: 0px; }"
        self.clearButton.setStyleSheet(style)
        self.clearButton.hide()
        self.clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)

    def setup_list_button (self):
        """Initialize the dropdown list button."""
        self.listButton = QtGui.QToolButton(self)
        pixmap = QtGui.QPixmap(":/icons/arrow_down.png")
        self.listButton.setIcon(QtGui.QIcon(pixmap))
        self.listButton.setIconSize(pixmap.size())
        self.listButton.setCursor(QtCore.Qt.ArrowCursor)
        style = "QToolButton { border: none; padding: 0px; }"
        self.listButton.setStyleSheet(style)
        self.listButton.hide()
        self.listButton.clicked.connect(self.toggle_list)

    def setModel (self, model):
        """Set list model for list of recent documents."""
        self.listmodel = model
        self.listview = QtGui.QListView()
        self.listview.setModel(model)
        self.listview.setWindowFlags(QtCore.Qt.Popup)
        self.listview.setFocusPolicy(QtCore.Qt.NoFocus)
        self.listview.setFocusProxy(self)
        self.listview.setMouseTracking(True)
        self.listview.setUniformItemSizes(True)
        self.listview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listview.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.listview.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Plain)
        self.listview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listview.installEventFilter(self)
        self.listview.clicked.connect(self.selectRecentDocument)
        self.listview.hide()
        updatefunc = lambda parent, start, end: self.updateListButton
        self.listmodel.rowsInserted.connect(updatefunc)
        self.listmodel.rowsRemoved.connect(updatefunc)
        self.updateListButton()

    def eventFilter(self, obj, event):
        """Handle events from the listview popup."""
        if obj != self.listview:
            return False

        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.listview.hide()
            self.setFocus()
            return True

        if event.type() == QtCore.QEvent.KeyPress:
            consumed = False
            key = event.key()
            if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.doneCompletion()
                consumed = True
            elif key == QtCore.Qt.Key_Escape:
                self.setFocus()
                self.listview.hide()
                consumed = True
            elif key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                         QtCore.Qt.Key_Home, QtCore.Qt.Key_End,
                         QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown):
                pass
            else:
                self.setFocus()
                self.event(event)
                self.listview.hide()
            return consumed
        return False

    def selectRecentDocument (self, index):
        """Select recent document text after click on the list view."""
        self.listview.hide()
        item = self.listmodel.data(index)
        text = unicode(item.toString())
        self.setText(text)

    def setup_size_metrics (self):
        """Set widget size including the buttons."""
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        padding_right = self.clearButton.sizeHint().width() + frameWidth + 1
        padding_left = self.listButton.sizeHint().width() + frameWidth + 1
        style = "QLineEdit { padding-left: %dpx; padding-right: %dpx } " % (
          padding_left, padding_right)
        self.setStyleSheet(style)
        # minimum width
        minSize = self.minimumSizeHint()
        buttonWidth = padding_left + padding_right
        minWidth = max(minSize.width(), buttonWidth)
        # minimum height
        buttonHeight = max(self.clearButton.sizeHint().height(),
                           self.listButton.sizeHint().height())
        minHeight = max(minSize.height(), buttonHeight + frameWidth*2)
        # set minimum size
        self.setMinimumSize(minWidth, minHeight)

    def resizeEvent (self, event):
        """Move the buttons due to resize event."""
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        bottom = self.rect().y() + self.rect().height()
        # clear button
        sizeHint = self.clearButton.sizeHint()
        x = self.rect().right() - frameWidth - sizeHint.width()
        y = (bottom - sizeHint.height()) / 2
        self.clearButton.move(x,y)
        # list button
        sizeHint = self.listButton.sizeHint()
        # add one to x and y since the button icon is a little off
        x = self.rect().left() + frameWidth + 1
        y = (bottom - sizeHint.height()) / 2 + 1
        self.listButton.move(x,y)

    def updateListButton (self):
        """Show or hide button for list of documents."""
        self.listButton.setVisible(bool(self.listmodel.rowCount()))

    def updateCloseButton (self, text):
        """Only display the clear button if there is some text."""
        self.clearButton.setVisible(bool(text))

    def toggle_list (self):
        """Show or hide list of documents."""
        if self.listview.isHidden():
            self.listview.adjustSize()
            point = self.mapToGlobal(QtCore.QPoint(0, self.height()))
            self.listview.move(point)
            self.listview.setFocus()
            self.listview.show()
        else:
            self.listview.hide()

    def addMenuEntries (self, menu):
        """Add browser bookmark actions to menu."""
        name = _("Insert %(browser)s bookmark file")
        if find_firefox():
            action = menu.addAction(name % {"browser": u"Firefox"})
            action.triggered.connect(lambda: self.setText(find_firefox()))
        if find_chrome():
            action = menu.addAction(name % {"browser": u"Google Chrome"})
            action.triggered.connect(lambda: self.setText(find_chrome()))
        if find_chromium():
            action = menu.addAction(name % {"browser": u"Chromium"})
            action.triggered.connect(lambda: self.setText(find_chromium()))
        if find_opera():
            action = menu.addAction(name % {"browser": u"Opera"})
            action.triggered.connect(lambda: self.setText(find_opera()))
        if find_safari():
            action = menu.addAction(name % {"browser": u"Safari"})
            action.triggered.connect(lambda: self.setText(find_safari()))

    def contextMenuEvent (self, event):
        """Handle context menu event."""
        menu = self.createStandardContextMenu()
        self.addMenuEntries(menu)
        menu.exec_(event.globalPos())


def find_firefox ():
    """Return Firefox bookmark filename or empty string if not found."""
    from ..bookmarks.firefox import find_bookmark_file
    return find_bookmark_file()


def find_chrome ():
    """Return Google Chrome bookmark filename or empty string if not found."""
    from ..bookmarks.chrome import find_bookmark_file
    return find_bookmark_file()


def find_chromium ():
    """Return Chromium bookmark filename or empty string if not found."""
    from ..bookmarks.chromium import find_bookmark_file
    return find_bookmark_file()


def find_opera ():
    """Return Opera bookmark filename or empty string if not found."""
    from ..bookmarks.opera import find_bookmark_file
    return find_bookmark_file()


def find_safari ():
    """Return Safari bookmark filename or empty string if not found."""
    from ..bookmarks.safari import find_bookmark_file
    return find_bookmark_file()
