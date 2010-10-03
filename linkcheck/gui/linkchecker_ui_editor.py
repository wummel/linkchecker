# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/editor.ui'
#
# Created: Sun Oct  3 09:27:19 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_EditorDialog(object):
    def setupUi(self, EditorDialog):
        EditorDialog.setObjectName("EditorDialog")
        EditorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        EditorDialog.resize(640, 600)
        self.verticalLayout = QtGui.QVBoxLayout(EditorDialog)
        self.verticalLayout.setObjectName("verticalLayout")

        self.retranslateUi(EditorDialog)
        QtCore.QMetaObject.connectSlotsByName(EditorDialog)

    def retranslateUi(self, EditorDialog):
        EditorDialog.setWindowTitle(_("LinkChecker source view"))

