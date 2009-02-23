# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/progress.ui'
#
# Created: Mon Feb 23 22:14:22 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ProgressDialog(object):
    def setupUi(self, ProgressDialog):
        ProgressDialog.setObjectName("ProgressDialog")
        ProgressDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ProgressDialog.resize(438, 420)
        self.cancelButton = QtGui.QPushButton(ProgressDialog)
        self.cancelButton.setGeometry(QtCore.QRect(260, 190, 75, 27))
        self.cancelButton.setObjectName("cancelButton")
        self.frame = QtGui.QFrame(ProgressDialog)
        self.frame.setGeometry(QtCore.QRect(40, 20, 301, 161))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.progressBar = QtGui.QProgressBar(self.frame)
        self.progressBar.setGeometry(QtCore.QRect(10, 120, 281, 23))
        self.progressBar.setProperty("value", QtCore.QVariant(24))
        self.progressBar.setObjectName("progressBar")
        self.tabWidget = QtGui.QTabWidget(self.frame)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 281, 101))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.label = QtGui.QLabel(self.tab)
        self.label.setGeometry(QtCore.QRect(10, 10, 48, 17))
        self.label.setObjectName("label")
        self.label_active = QtGui.QLabel(self.tab)
        self.label_active.setGeometry(QtCore.QRect(80, 10, 48, 17))
        self.label_active.setObjectName("label_active")
        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setGeometry(QtCore.QRect(10, 30, 48, 17))
        self.label_2.setObjectName("label_2")
        self.label_queued = QtGui.QLabel(self.tab)
        self.label_queued.setGeometry(QtCore.QRect(80, 30, 48, 17))
        self.label_queued.setObjectName("label_queued")
        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setGeometry(QtCore.QRect(10, 50, 48, 17))
        self.label_3.setObjectName("label_3")
        self.label_checked = QtGui.QLabel(self.tab)
        self.label_checked.setGeometry(QtCore.QRect(80, 50, 48, 17))
        self.label_checked.setObjectName("label_checked")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.scrollArea = QtGui.QScrollArea(self.tab_2)
        self.scrollArea.setGeometry(QtCore.QRect(0, 0, 271, 71))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 267, 67))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.textBrowser = QtGui.QTextBrowser(self.scrollAreaWidgetContents)
        self.textBrowser.setGeometry(QtCore.QRect(0, 0, 271, 71))
        self.textBrowser.setObjectName("textBrowser")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.tabWidget.addTab(self.tab_2, "")

        self.retranslateUi(ProgressDialog)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(ProgressDialog)

    def retranslateUi(self, ProgressDialog):
        ProgressDialog.setWindowTitle(QtGui.QApplication.translate("ProgressDialog", "LinkChecker progress", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("ProgressDialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ProgressDialog", "Active:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_active.setText(QtGui.QApplication.translate("ProgressDialog", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ProgressDialog", "Queued:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_queued.setText(QtGui.QApplication.translate("ProgressDialog", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ProgressDialog", "Checked:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_checked.setText(QtGui.QApplication.translate("ProgressDialog", "0", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("ProgressDialog", "Status", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("ProgressDialog", "Debug", None, QtGui.QApplication.UnicodeUTF8))

