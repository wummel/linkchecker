# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/progress.ui'
#
# Created: Wed Mar 16 18:06:04 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ProgressDialog(object):
    def setupUi(self, ProgressDialog):
        ProgressDialog.setObjectName(_fromUtf8("ProgressDialog"))
        ProgressDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ProgressDialog.resize(252, 179)
        self.verticalLayout = QtGui.QVBoxLayout(ProgressDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(ProgressDialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.groupBox = QtGui.QGroupBox(self.frame)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.label_active = QtGui.QLabel(self.groupBox)
        self.label_active.setObjectName(_fromUtf8("label_active"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.label_active)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.label_queued = QtGui.QLabel(self.groupBox)
        self.label_queued.setObjectName(_fromUtf8("label_queued"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.label_queued)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.label_checked = QtGui.QLabel(self.groupBox)
        self.label_checked.setObjectName(_fromUtf8("label_checked"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.label_checked)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.progressBar = QtGui.QProgressBar(self.frame)
        self.progressBar.setProperty(_fromUtf8("value"), 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout_2.addWidget(self.progressBar)
        self.widget = QtGui.QWidget(self.frame)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.cancelLabel = QtGui.QLabel(self.widget)
        self.cancelLabel.setText(_fromUtf8(""))
        self.cancelLabel.setObjectName(_fromUtf8("cancelLabel"))
        self.horizontalLayout.addWidget(self.cancelLabel)
        self.cancelButton = QtGui.QPushButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cancelButton.sizePolicy().hasHeightForWidth())
        self.cancelButton.setSizePolicy(sizePolicy)
        self.cancelButton.setObjectName(_fromUtf8("cancelButton"))
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout_2.addWidget(self.widget)
        self.verticalLayout.addWidget(self.frame)
        self.cancelLabel.setBuddy(self.cancelButton)

        self.retranslateUi(ProgressDialog)
        QtCore.QMetaObject.connectSlotsByName(ProgressDialog)

    def retranslateUi(self, ProgressDialog):
        ProgressDialog.setWindowTitle(_("LinkChecker progress"))
        self.groupBox.setTitle(_("Status"))
        self.label.setText(_("Active:"))
        self.label_active.setText(_("0"))
        self.label_2.setText(_("Queued:"))
        self.label_queued.setText(_("0"))
        self.label_3.setText(_("Checked:"))
        self.label_checked.setText(_("0"))
        self.cancelButton.setText(_("Cancel"))

