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
from .properties import PropertiesDialog
from .progress import LinkCheckerProgress, StatusLogger
from .debug import LinkCheckerDebug
from .logger import GuiLogger, GuiLogHandler
from .help import HelpWindow
from .options import LinkCheckerOptions
from .checker import CheckerThread
from .contextmenu import ContextMenu
from .editor import EditorWindow
from .urlmodel import UrlItem, UrlItemModel
from .. import configuration, checker, director, add_intern_pattern, \
    strformat, fileutil
from ..containers import enum
from .. import url as urlutil
from ..checker import httpheaders


DocBaseUrl = "qthelp://bfk.app.linkchecker/doc/"
RegistryBase = "Bastian"
Status = enum('idle', 'checking')


def save_point (qpoint):
    """Ensure positive X and Y values of point."""
    qpoint.setX(max(0, qpoint.x()))
    qpoint.setY(max(0, qpoint.y()))
    return qpoint


def save_size (qsize):
    """Ensure minimum width and height values of the given size."""
    qsize.setWidth(max(400, qsize.width()))
    qsize.setHeight(max(400, qsize.height()))
    return qsize


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
        self.debug = LinkCheckerDebug(parent=self)
        self.checker = CheckerThread()
        self.contextmenu = ContextMenu(parent=self)
        self.editor = EditorWindow(parent=self)
        self.properties = PropertiesDialog(parent=self)
        # Note: we can't use QT assistant here because of the .exe packaging
        self.assistant = HelpWindow(self, self.get_qhcpath())
        self.init_treeview()
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
            self.resize(save_size(settings.value('size').toSize()))
            self.move(save_point(settings.value('pos').toPoint()))
        settings.endGroup()

    def connect_widgets (self):
        """Connect widget signals. Some signals use the AutoConnect feature.
        Autoconnected methods have the form on_<objectname>_<signal>.
        """
        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("log_url(PyQt_PyObject)"), self.log_url)

    def init_treeview (self):
        self.model = UrlItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setColumnHidden(0, True)
        self.treeView.setColumnWidth(1, 200)
        self.treeView.setColumnWidth(2, 200)
        self.treeView.setColumnWidth(3, 150)
        #self.setForeground(4, QtGui.QBrush(url_item.color))
        self.treeView.setSortingEnabled(True)
        self.treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
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
            self.debug.reset()
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
        settings.setValue("size", QtCore.QVariant(save_size(self.size())))
        settings.setValue("pos", QtCore.QVariant(save_point(self.pos())))
        settings.endGroup()
        settings.sync()
        if e is not None:
            e.accept()
        # remove registered logging handler
        self.config.remove_loghandler(self.handler)

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

    @QtCore.pyqtSignature("")
    def on_actionDebug_triggered (self):
        """Display debug dialog."""
        self.debug.show()

    def on_controlButton_clicked (self):
        """Start a new check."""
        if self.status == Status.idle:
            self.check()

    def check (self):
        """Check given URL."""
        self.controlButton.setEnabled(False)
        self.model.clear()
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
        self.handler = GuiLogHandler(self.debug)
        self.config["status"] = True
        self.config["status_wait_seconds"] = 1
        self.config.init_logging(StatusLogger(self.progress), handler=self.handler)

    def set_config (self):
        """Set configuration."""
        self.config["recursionlevel"] = self.options.recursionlevel.value()
        self.config["verbose"] = self.options.verbose.isChecked()
        self.config["timeout"] = self.options.timeout.value()
        self.config["threads"] = self.options.threads.value()
        if self.options.debug.isChecked():
            self.config.set_debug(["all"])
            # make sure at least one thread is used
            self.config["threads"] = 1
        else:
            self.config.reset_loglevel()

    def log_url (self, url_data):
        """Add URL data to tree widget."""
        self.model.addUrlItem(UrlItem(url_data, self.num))
        self.num += 1

    def view_item_properties (self, item):
        self.properties.set_item(item)
        self.properties.show()

    def on_treeView_doubleClicked (self, index):
        """View property page."""
        urlitem = self.model.getUrlItem(index)
        if urlitem is not None:
            self.view_item_properties(urlitem)

    def on_treeView_customContextMenuRequested (self, point):
        """Show item context menu."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            self.contextmenu.enableFromItem(urlitem)
            self.contextmenu.popup(QtGui.QCursor.pos())

    @QtCore.pyqtSignature("")
    def on_actionViewProperties_triggered (self):
        """View URL data properties in a separate window."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            self.view_item_properties(urlitem)

    @QtCore.pyqtSignature("")
    def on_actionViewOnline_triggered (self):
        """View item URL online."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            webbrowser.open(urlitem.url_data.url)

    @QtCore.pyqtSignature("")
    def on_actionViewParentOnline_triggered (self):
        """View item parent URL online."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            webbrowser.open(urlitem.url_data.parent_url)

    @QtCore.pyqtSignature("")
    def on_actionViewParentSource_triggered (self):
        """View item parent URL source in local text editor (read-only)."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            self.view_source(urlitem.url_data.parent_url,
                             urlitem.url_data.line, urlitem.url_data.column)

    def view_source (self, url, line, col):
        self.editor.setWindowTitle(u"View %s" % url)
        info, data = urlutil.get_content(url, proxy=self.config["proxy"])
        if (info, data) == (None, None):
            self.editor.setText(u"An error occurred retreiving URL `%s'." % url)
        else:
            content_type = httpheaders.get_content_type(info)
            if not content_type:
                # read function for content type guessing
                read = lambda: data
                content_type = fileutil.guess_mimetype(url, read=read)
            self.editor.setContentType(content_type)
            self.editor.setText(data, line=line, col=col)
        self.editor.show()

    @QtCore.pyqtSignature("")
    def on_actionCopyToClipboard_triggered (self):
        """Copy item URL to clipboard."""
        index = self.treeView.currentIndex()
        urlitem = self.model.data(index)
        if urlitem:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(urlitem.url_data.url)
            event = QtCore.QEvent(QtCore.QEvent.Clipboard)
            QtGui.QApplication.sendEvent(clipboard, event)

    def set_statusbar (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)
