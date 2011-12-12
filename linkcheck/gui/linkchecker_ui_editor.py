# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/editor.ui'
#
# Created: Mon Dec 12 19:00:37 2011
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_EditorDialog(object):
    def setupUi(self, EditorDialog):
        EditorDialog.setObjectName(_fromUtf8("EditorDialog"))
        EditorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        EditorDialog.resize(640, 600)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(EditorDialog.sizePolicy().hasHeightForWidth())
        EditorDialog.setSizePolicy(sizePolicy)
        EditorDialog.setWindowTitle(_("LinkChecker source view"))
        self.verticalLayout = QtGui.QVBoxLayout(EditorDialog)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.menubar = QtGui.QMenuBar(EditorDialog)
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setTitle(_("&File"))
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.verticalLayout.addWidget(self.menubar)
        self.frame = QtGui.QFrame(EditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.frame.setFrameShadow(QtGui.QFrame.Plain)
        self.frame.setLineWidth(0)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout.addWidget(self.frame)
        self.actionSave = QtGui.QAction(EditorDialog)
        self.actionSave.setText(_("&Save"))
        self.actionSave.setShortcut(_("Ctrl+S"))
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.menuFile.addAction(self.actionSave)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(EditorDialog)
        QtCore.QMetaObject.connectSlotsByName(EditorDialog)

    def retranslateUi(self, EditorDialog):
        pass

