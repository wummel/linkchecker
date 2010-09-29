# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2010 Bastian Kleineidam
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

import os
import sys
import webbrowser
from PyQt4 import QtCore, QtGui
from .linkchecker_ui_main import Ui_MainWindow
from .progress import LinkCheckerProgress, StatusLogger
from .logger import GuiLogger, GuiLogHandler
from .help import HelpWindow
from .options import LinkCheckerOptions
from .checker import CheckerThread
from .contextmenu import ContextMenu
from .. import configuration, checker, director, add_intern_pattern, \
    strformat
from ..containers import enum


DocBaseUrl = "qthelp://bfk.app.linkchecker/doc/"
RegistryBase = "Bastian"
Status = enum('idle', 'checking')


class LinkCheckerMain (QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None, url=None):
        """Initialize UI."""
        super(LinkCheckerMain, self).__init__(parent)
        self.setupUi(self)
        if url:
            self.urlinput.setText(url)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(configuration.App)
        # init subdialogs
        self.options = LinkCheckerOptions(parent=self)
        self.progress = LinkCheckerProgress(parent=self)
        self.checker = CheckerThread()
        self.contextmenu = ContextMenu(parent=self)
        # Note: we can't use QT assistant here because of the .exe packaging
        self.assistant = HelpWindow(self, self.get_qhcpath())
        # setup this widget
        self.init_treewidget()
        self.read_settings()
        self.connect_widgets()
        self.init_config()
        self.status = Status.idle

    def get_qhcpath (self):
        paths = [
            # when developing
            os.path.join(configuration.configdata.install_data, "doc", "html"),
            # when running under py2exe
            os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "share", "linkchecker"),
            # after installing as a package
            configuration.configdata.config_dir,
        ]
        for path in paths:
            qhcfile = os.path.join(path, "lccollection.qhc")
            if os.path.isfile(qhcfile):
                break
        return qhcfile

    def read_settings (self):
        settings = QtCore.QSettings(RegistryBase, configuration.AppName)
        settings.beginGroup('mainwindow')
        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
            self.move(settings.value('pos').toPoint())
        settings.endGroup()

    def connect_widgets (self):
        """Connect widget signals. Some signals use the AutoConnect feature.
        Autoconnected methods have the form on_<objectname>_<signal>.
        """
        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("log_url(PyQt_PyObject)"), self.log_url)
        #self.controlButton.setText(_("Start"))
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap(":/icons/start.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #icon = self.style().standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        #self.controlButton.setIcon(icon)

    def init_treewidget (self):
        self.treeWidget.setColumnHidden(0, True)
        self.treeWidget.setColumnWidth(1, 200)
        self.treeWidget.setColumnWidth(2, 200)
        self.treeWidget.setColumnWidth(3, 150)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.num = 0

    def get_status (self):
        return self._status

    def set_status (self, status):
        self._status = status
        if status == Status.idle:
            self.progress.hide()
            self.aggregate = None
            self.controlButton.setEnabled(True)
            self.set_statusbar(_("Ready."))
        elif status == Status.checking:
            self.num = 0
            self.progress.reset()
            self.progress.show()
            self.controlButton.setEnabled(False)

    status = property(get_status, set_status)

    def set_status_idle (self):
        """Set idle status. Helper function for signal connections."""
        self.status = Status.idle

    @QtCore.pyqtSignature("")
    def on_actionHelp_triggered (self):
        """Show help page."""
        url = QtCore.QUrl("%sindex.html" % DocBaseUrl)
        self.assistant.showDocumentation(url)

    @QtCore.pyqtSignature("")
    def on_actionOptions_triggered (self):
        """Show option dialog."""
        self.options.exec_()

    @QtCore.pyqtSignature("")
    def on_actionQuit_triggered (self):
        """Quit application."""
        self.close()

    def closeEvent (self, e=None):
        """Save settings on close."""
        settings = QtCore.QSettings(RegistryBase, configuration.AppName)
        settings.beginGroup('mainwindow')
        settings.setValue("size", QtCore.QVariant(self.size()))
        settings.setValue("pos", QtCore.QVariant(self.pos()))
        settings.endGroup()
        settings.sync()
        if e is not None:
            e.accept()

    @QtCore.pyqtSignature("")
    def on_actionAbout_triggered (self):
        """Display about dialog."""
        d = {
            "app": configuration.App,
            "appname": configuration.AppName,
            "copyright": configuration.HtmlCopyright,
        }
        QtGui.QMessageBox.about(self, _(u"About %(appname)s") % d,
            _(u"""<qt><p>%(appname)s checks HTML documents and websites
for broken links.</p>
<p>%(copyright)s</p>
<p>%(app)s is licensed under the
<a href="http://www.gnu.org/licenses/gpl.html">GPL</a>
Version 2 or later.</p>
</qt>""") % d)

    def on_controlButton_clicked (self):
        """Start a new check."""
        if self.status == Status.idle:
            self.check()

    def check (self):
        """Check given URL."""
        self.controlButton.setEnabled(False)
        self.treeWidget.clear()
        self.set_config()
        aggregate = director.get_aggregate(self.config)
        url = unicode(self.urlinput.text()).strip()
        if not url:
            self.set_statusbar(_("Error, empty URL"))
            self.status = Status.idle
            return
        if url.startswith(u"www."):
            url = u"http://%s" % url
        elif url.startswith(u"ftp."):
            url = u"ftp://%s" % url
        self.set_statusbar(_("Checking '%s'.") % strformat.limit(url, 40))
        url_data = checker.get_url_from(url, 0, aggregate)
        try:
            add_intern_pattern(url_data, self.config)
        except UnicodeError:
            self.set_statusbar(_("Error, invalid URL `%s'.") %
                                  strformat.limit(url, 40))
            self.status = Status.idle
            return
        aggregate.urlqueue.put(url_data)
        self.aggregate = aggregate
        # check in background
        self.checker.check(self.aggregate, self.progress)
        self.status = Status.checking

    def init_config (self):
        """Create a configuration object."""
        self.config = configuration.Configuration()
        self.config.logger_add("gui", GuiLogger)
        self.config["logger"] = self.config.logger_new('gui', widget=self.checker)
        handler = GuiLogHandler(self.checker)
        self.config["status"] = True
        self.config["status_wait_seconds"] = 1
        self.config.init_logging(StatusLogger(self.progress), handler=handler)

    def set_config (self):
        """Set configuration."""
        self.config["recursionlevel"] = self.options.recursionlevel.value()
        self.config["verbose"] = self.options.verbose.isChecked()
        self.config["timeout"] = self.options.timeout.value()
        self.config["threads"] = self.options.threads.value()

    def log_url (self, url_data):
        """Add URL data to tree widget."""
        num = u"%09d" % self.num
        if url_data.parent_url:
            parent = unicode(url_data.parent_url) + \
                (_(", line %d") % url_data.line) + \
                (_(", col %d") % url_data.column)
        else:
            parent = u""
        url = unicode(url_data.url)
        name = url_data.name
        if url_data.valid:
            if url_data.warnings:
                color = QtCore.Qt.darkYellow
            else:
                color = QtCore.Qt.darkGreen
            result = u"Valid"
        else:
            color = QtCore.Qt.darkRed
            result = u"Error"
        if url_data.result:
            result += u": %s" % url_data.result
        item = QtGui.QTreeWidgetItem((num, parent, url, name, result))
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        item.setForeground(4, QtGui.QBrush(color))
        item.setToolTip(2, url)
        item.setToolTip(3, name)
        if url_data.warnings:
            text = u"\n".join(url_data.warnings)
            item.setToolTip(4, strformat.wrap(text, 60))
        self.treeWidget.addTopLevelItem(item)
        self.num += 1

    def on_treeWidget_itemDoubleClicked (self, item, column):
        """View property page."""
        pass # XXX todo

    def on_treeWidget_customContextMenuRequested (self, point):
        """Show item context menu."""
        item = self.treeWidget.itemAt(point)
        if item is not None:
            self.contextmenu.popup(QtGui.QCursor.pos())

    @QtCore.pyqtSignature("")
    def on_actionViewOnline_triggered (self):
        """View item URL online."""
        item = self.treeWidget.currentItem()
        if item is not None:
            url = str(item.text(2))
            webbrowser.open(url)

    @QtCore.pyqtSignature("")
    def on_actionCopyToClipboard_triggered (self):
        """Copy URL to clipboard."""
        item = self.treeWidget.currentItem()
        if item is not None:
            url = str(item.text(2))
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(url)
            event = QtCore.QEvent(QtCore.QEvent.Clipboard)
            QtGui.QApplication.sendEvent(clipboard, event)

    def set_statusbar (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)
