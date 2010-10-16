# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/debug.ui'
#
# Created: Sat Oct 16 19:17:16 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_DebugDialog(object):
    def setupUi(self, DebugDialog):
        DebugDialog.setObjectName("DebugDialog")
        DebugDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        DebugDialog.resize(564, 547)
        self.verticalLayout = QtGui.QVBoxLayout(DebugDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtGui.QFrame(DebugDialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textEdit = QtGui.QPlainTextEdit(self.frame)
        self.textEdit.setUndoRedoEnabled(False)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlainText("None")
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout_2.addWidget(self.textEdit)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(DebugDialog)
        QtCore.QMetaObject.connectSlotsByName(DebugDialog)

    def retranslateUi(self, DebugDialog):
        DebugDialog.setWindowTitle(_("LinkChecker debug log"))

