# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/options.ui'
#
# Created: Sun Jan 11 11:30:58 2009
#      by: PyQt4 UI code generator 4.4.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Options(object):
    def setupUi(self, Options):
        Options.setObjectName("Options")
        Options.resize(306,255)
        self.resetButton = QtGui.QPushButton(Options)
        self.resetButton.setGeometry(QtCore.QRect(200,220,91,27))
        self.resetButton.setObjectName("resetButton")
        self.frame = QtGui.QFrame(Options)
        self.frame.setGeometry(QtCore.QRect(9,9,288,201))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.recursionlevel = QtGui.QSpinBox(self.frame)
        self.recursionlevel.setGeometry(QtCore.QRect(130,20,46,23))
        self.recursionlevel.setMinimum(-1)
        self.recursionlevel.setMaximum(100)
        self.recursionlevel.setProperty("value",QtCore.QVariant(-1))
        self.recursionlevel.setObjectName("recursionlevel")
        self.label = QtGui.QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(30,20,111,20))
        self.label.setObjectName("label")
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setGeometry(QtCore.QRect(30,60,91,17))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtGui.QLabel(self.frame)
        self.label_3.setGeometry(QtCore.QRect(30,100,48,17))
        self.label_3.setObjectName("label_3")
        self.timeout = QtGui.QSpinBox(self.frame)
        self.timeout.setGeometry(QtCore.QRect(130,100,81,23))
        self.timeout.setMinimum(2)
        self.timeout.setMaximum(300)
        self.timeout.setProperty("value",QtCore.QVariant(60))
        self.timeout.setObjectName("timeout")
        self.label_5 = QtGui.QLabel(self.frame)
        self.label_5.setGeometry(QtCore.QRect(30,140,101,17))
        self.label_5.setObjectName("label_5")
        self.threads = QtGui.QSpinBox(self.frame)
        self.threads.setGeometry(QtCore.QRect(130,140,46,23))
        self.threads.setMinimum(1)
        self.threads.setMaximum(20)
        self.threads.setProperty("value",QtCore.QVariant(10))
        self.threads.setObjectName("threads")
        self.verbose = QtGui.QCheckBox(self.frame)
        self.verbose.setEnabled(True)
        self.verbose.setGeometry(QtCore.QRect(130,60,31,22))
        self.verbose.setObjectName("verbose")
        self.closeButton = QtGui.QPushButton(Options)
        self.closeButton.setGeometry(QtCore.QRect(10,220,75,27))
        self.closeButton.setObjectName("closeButton")

        self.retranslateUi(Options)
        QtCore.QMetaObject.connectSlotsByName(Options)

    def retranslateUi(self, Options):
        Options.setWindowTitle(QtGui.QApplication.translate("Options", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.resetButton.setToolTip(QtGui.QApplication.translate("Options", "Reset all options to default values.", None, QtGui.QApplication.UnicodeUTF8))
        self.resetButton.setText(QtGui.QApplication.translate("Options", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.recursionlevel.setToolTip(QtGui.QApplication.translate("Options", "Check recursively all links up to given depth. A negative depth will enable infinite recursion.", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setToolTip(QtGui.QApplication.translate("Options", "Check recursively all links up to given depth. A negative depth will enable infinite recursion.", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Options", "Recursive depth", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setToolTip(QtGui.QApplication.translate("Options", "Log all checked URLs once. Default is to log only errors and warnings.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Options", "Verbose output", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setToolTip(QtGui.QApplication.translate("Options", "Set the timeout for connection attempts in seconds.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Options", "Timeout", None, QtGui.QApplication.UnicodeUTF8))
        self.timeout.setToolTip(QtGui.QApplication.translate("Options", "Set the timeout for connection attempts in seconds.", None, QtGui.QApplication.UnicodeUTF8))
        self.timeout.setSuffix(QtGui.QApplication.translate("Options", " seconds", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setToolTip(QtGui.QApplication.translate("Options", "Generate no more than the given number of threads.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Options", "Number of threads", None, QtGui.QApplication.UnicodeUTF8))
        self.threads.setToolTip(QtGui.QApplication.translate("Options", "Generate no more than the given number of threads.", None, QtGui.QApplication.UnicodeUTF8))
        self.verbose.setToolTip(QtGui.QApplication.translate("Options", "Log all checked URLs once. Default is to log only errors and warnings.", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate("Options", "Close", None, QtGui.QApplication.UnicodeUTF8))

