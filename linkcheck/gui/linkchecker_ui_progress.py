# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/progress.ui'
#
# Created: Wed Feb 18 23:25:25 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ProgressDialog(object):
    def setupUi(self, ProgressDialog):
        ProgressDialog.setObjectName("ProgressDialog")
        ProgressDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ProgressDialog.resize(505, 232)
        self.cancelButton = QtGui.QPushButton(ProgressDialog)
        self.cancelButton.setGeometry(QtCore.QRect(390, 190, 75, 27))
        self.cancelButton.setObjectName("cancelButton")
        self.frame = QtGui.QFrame(ProgressDialog)
        self.frame.setGeometry(QtCore.QRect(40, 20, 451, 161))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.progressBar = QtGui.QProgressBar(self.frame)
        self.progressBar.setGeometry(QtCore.QRect(30, 120, 391, 23))
        self.progressBar.setProperty("value", QtCore.QVariant(24))
        self.progressBar.setObjectName("progressBar")
        self.scrollArea = QtGui.QScrollArea(self.frame)
        self.scrollArea.setGeometry(QtCore.QRect(30, 10, 391, 94))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 387, 90))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.textBrowser = QtGui.QTextBrowser(self.scrollAreaWidgetContents)
        self.textBrowser.setGeometry(QtCore.QRect(0, 0, 391, 94))
        self.textBrowser.setObjectName("textBrowser")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.retranslateUi(ProgressDialog)
        QtCore.QMetaObject.connectSlotsByName(ProgressDialog)

    def retranslateUi(self, ProgressDialog):
        ProgressDialog.setWindowTitle(QtGui.QApplication.translate("ProgressDialog", "LinkChecker progress", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("ProgressDialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

