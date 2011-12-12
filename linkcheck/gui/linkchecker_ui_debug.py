# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/debug.ui'
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

class Ui_DebugDialog(object):
    def setupUi(self, DebugDialog):
        DebugDialog.setObjectName(_fromUtf8("DebugDialog"))
        DebugDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        DebugDialog.resize(564, 547)
        DebugDialog.setWindowTitle(_("LinkChecker debug log"))
        self.verticalLayout = QtGui.QVBoxLayout(DebugDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(DebugDialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.textEdit = QtGui.QPlainTextEdit(self.frame)
        self.textEdit.setUndoRedoEnabled(False)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlainText(_fromUtf8(""))
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout_2.addWidget(self.textEdit)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(DebugDialog)
        QtCore.QMetaObject.connectSlotsByName(DebugDialog)

    def retranslateUi(self, DebugDialog):
        pass

