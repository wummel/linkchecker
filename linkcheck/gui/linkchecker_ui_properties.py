# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/properties.ui'
#
# Created: Fri Nov  5 13:01:36 2010
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PropertiesDialog(object):
    def setupUi(self, PropertiesDialog):
        PropertiesDialog.setObjectName("PropertiesDialog")
        PropertiesDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        PropertiesDialog.resize(564, 547)
        self.verticalLayout = QtGui.QVBoxLayout(PropertiesDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtGui.QFrame(PropertiesDialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.label = QtGui.QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(30, 40, 45, 16))
        self.label.setObjectName("label")
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setGeometry(QtCore.QRect(30, 70, 45, 13))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtGui.QLabel(self.frame)
        self.label_3.setGeometry(QtCore.QRect(30, 100, 45, 13))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtGui.QLabel(self.frame)
        self.label_4.setGeometry(QtCore.QRect(30, 150, 71, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtGui.QLabel(self.frame)
        self.label_5.setGeometry(QtCore.QRect(30, 180, 45, 13))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtGui.QLabel(self.frame)
        self.label_6.setGeometry(QtCore.QRect(30, 210, 45, 13))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtGui.QLabel(self.frame)
        self.label_7.setGeometry(QtCore.QRect(30, 240, 71, 16))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtGui.QLabel(self.frame)
        self.label_8.setGeometry(QtCore.QRect(30, 270, 45, 13))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtGui.QLabel(self.frame)
        self.label_9.setGeometry(QtCore.QRect(30, 300, 45, 13))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtGui.QLabel(self.frame)
        self.label_10.setGeometry(QtCore.QRect(30, 330, 45, 13))
        self.label_10.setObjectName("label_10")
        self.label_11 = QtGui.QLabel(self.frame)
        self.label_11.setGeometry(QtCore.QRect(30, 360, 45, 13))
        self.label_11.setObjectName("label_11")
        self.label_12 = QtGui.QLabel(self.frame)
        self.label_12.setGeometry(QtCore.QRect(30, 380, 45, 13))
        self.label_12.setObjectName("label_12")
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(PropertiesDialog)
        QtCore.QMetaObject.connectSlotsByName(PropertiesDialog)

    def retranslateUi(self, PropertiesDialog):
        PropertiesDialog.setWindowTitle(_("LinkChecker URL properties"))
        self.label.setText(_("ID"))
        self.label_2.setText(_("URL"))
        self.label_3.setText(_("Name"))
        self.label_4.setText(_("Parent URL"))
        self.label_5.setText(_("Base"))
        self.label_6.setText(_("Real URL"))
        self.label_7.setText(_("Check time"))
        self.label_8.setText(_("D/L time"))
        self.label_9.setText(_("Size"))
        self.label_10.setText(_("Info"))
        self.label_11.setText(_("Warning"))
        self.label_12.setText(_("Result"))

