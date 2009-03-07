# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2009 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from PyQt4 import QtCore, QtGui
from .linkchecker_ui_main import Ui_MainWindow
from .progress import LinkCheckerProgress, StatusLogger
from .logger import GuiLogger, GuiLogHandler
from .help import HelpWindow
from .options import LinkCheckerOptions
from .checker import CheckerThread
from .. import configuration, checker, director, add_intern_pattern, \
    strformat
from ..containers import enum


DocBaseUrl = "qthelp://bfk.app.linkchecker/doc/build/htmlhelp/"

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
        # Note: we can't use QT assistant here because of the .exe packaging
        self.assistant = HelpWindow(self, "doc/lccollection.qhc")
        # setup this widget
        self.init_treewidget()
        self.read_settings()
        self.connect_widgets()
        self.init_config()
        self.status = Status.idle

    def read_settings (self):
        settings = QtCore.QSettings('bfk', configuration.AppName)
        settings.beginGroup('mainwindow')
        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
            self.move(settings.value('pos').toPoint())
        settings.endGroup()

    def connect_widgets (self):
        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("log_url(PyQt_PyObject)"), self.log_url)
        self.connect(self.controlButton, QtCore.SIGNAL("clicked()"), self.start)
        self.connect(self.optionsButton, QtCore.SIGNAL("clicked()"), self.options.exec_)
        self.connect(self.actionQuit, QtCore.SIGNAL("triggered()"), self.close)
        self.connect(self.actionAbout, QtCore.SIGNAL("triggered()"), self.about)
        self.connect(self.actionHelp, QtCore.SIGNAL("triggered()"), self.showDocumentation)
        #self.controlButton.setText(_("Start"))
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap(":/icons/start.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
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
            self.optionsButton.setEnabled(True)
            self.set_statusbar(_("Ready."))
        elif status == Status.checking:
            self.num = 0
            self.progress.reset()
            self.progress.show()
            self.controlButton.setEnabled(False)
            self.optionsButton.setEnabled(False)

    status = property(get_status, set_status)

    def set_status_idle (self):
        """Set idle status. Helper function for signal connections."""
        self.status = Status.idle

    def showDocumentation (self):
        """Show help page."""
        url = QtCore.QUrl("%sindex.html" % DocBaseUrl)
        self.assistant.showDocumentation(url)

    def closeEvent (self, e=None):
        """Save settings on close."""
        settings = QtCore.QSettings('bfk', configuration.AppName)
        settings.beginGroup('mainwindow')
        settings.setValue("size", QtCore.QVariant(self.size()))
        settings.setValue("pos", QtCore.QVariant(self.pos()))
        settings.endGroup()
        settings.sync()
        if e is not None:
            e.accept()

    def about (self):
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

    def start (self):
        """Start a new check."""
        if self.status == Status.idle:
            self.check()

    def check (self):
        """Check given URL."""
        self.controlButton.setEnabled(False)
        self.optionsButton.setEnabled(False)
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
        item.setFlags(QtCore.Qt.NoItemFlags)
        item.setForeground(4, QtGui.QBrush(color))
        item.setToolTip(2, url)
        item.setToolTip(3, name)
        if url_data.warnings:
            text = u"\n".join(url_data.warnings)
            item.setToolTip(4, strformat.wrap(text, 60))
        self.treeWidget.addTopLevelItem(item)
        self.num += 1

    def set_statusbar (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)
