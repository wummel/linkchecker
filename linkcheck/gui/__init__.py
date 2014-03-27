# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008-2014 Bastian Kleineidam
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
import re
import webbrowser
from PyQt4 import QtCore, QtGui
from .linkchecker_ui_main import Ui_MainWindow
from .properties import set_properties, clear_properties
from .statistics import set_statistics, clear_statistics
from .debug import LinkCheckerDebug
from .logger import SignalLogger, GuiLogHandler, StatusLogger
from .help import HelpWindow
from .options import LinkCheckerOptions
from .checker import CheckerThread
from .contextmenu import ContextMenu
from .editor import EditorWindow
from .updater import UpdateDialog
from .urlmodel import UrlItemModel
from .urlsave import urlsave
from .settings import Settings
from .recentdocs import RecentDocumentModel
from .projects import openproject, saveproject, loadproject, ProjectExt
from .. import configuration, checker, director, get_link_pat, \
    strformat, fileutil, LinkCheckerError, i18n, httputil
from ..containers import enum
from .. import url as urlutil


DocBaseUrl = "qthelp://bfk.app.linkchecker/doc/"
RegistryBase = "Bastian"
Status = enum('idle', 'checking')

MaxMessageLength = 60

def get_app_style ():
    """Return appropriate QStyle object for the current platform to
    be used in QApplication.setStyle().
    Currently prefers Macintosh on OS X, else Plastique.
    Style names are case insensitive.

    See also
    http://doc.trolltech.com/latest/gallery-macintosh.html
    and
    http://doc.trolltech.com/latest/gallery-plastique.html
    """
    if sys.platform == 'darwin':
        style = "Macintosh"
    else:
        style = "Plastique"
    return QtGui.QStyleFactory.create(style)


def get_icon (name):
    """Return QIcon with given pixmap resource name."""
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(name), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    return icon


def warninglines2regex(lines):
    """Convert a list of strings to a regular expression matching any of
    the given strings."""
    return u"|".join([re.escape(line) for line in lines])


class LinkCheckerMain (QtGui.QMainWindow, Ui_MainWindow):
    """The main window displaying checked URLs."""

    log_url_signal = QtCore.pyqtSignal(object)
    log_status_signal = QtCore.pyqtSignal(int, int, int, float, int)
    log_stats_signal = QtCore.pyqtSignal(object)
    error_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, url=None, project=None):
        """Initialize UI."""
        super(LinkCheckerMain, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(configuration.App)
        # app settings
        self.settings = Settings(RegistryBase, configuration.AppName)
        # init subdialogs
        self.options = LinkCheckerOptions(parent=self)
        self.debug = LinkCheckerDebug(parent=self)
        self.checker = CheckerThread(parent=self)
        self.contextmenu = ContextMenu(parent=self)
        self.editor = EditorWindow(parent=self)
        # Note: do not use QT assistant here because of the .exe packaging
        self.assistant = HelpWindow(self, self.get_qhcpath())
        self.config_error = None
        self.icon_start = get_icon(":/icons/start.png")
        self.icon_stop = get_icon(":/icons/stop.png")
        self.movie = QtGui.QMovie(":/icons/busy.gif")
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        self.label_busy.setText(u"")
        self.label_busy.setMovie(self.movie)
        # init the rest
        self.init_url(url)
        self.init_treeview()
        self.connect_widgets()
        self.init_shortcuts()
        self.init_config()
        self.read_config()
        self.init_menu()
        self.init_drop()
        self.init_app(project)

    def init_url (self, url):
        """Initialize URL input."""
        documents = self.settings.read_recent_documents()
        self.recent = RecentDocumentModel(parent=self, documents=documents)
        self.urlinput.setModel(self.recent)
        if url:
            self.urlinput.setText(url)
        elif documents:
            self.urlinput.setText(documents[0])

    def init_menu (self):
        """Add menu entries for bookmark file checking."""
        self.urlinput.addMenuEntries(self.menuEdit)
        self.menuLang = self.menuEdit.addMenu(_('Languages'))
        self.menuLang.setTitle(_("&Language"))
        # ensure only one action is checked
        langActionGroup = QtGui.QActionGroup(self)
        langActionGroup.triggered.connect(self.switch_language)
        for i, lang in enumerate(sorted(i18n.supported_languages)):
            action = self.menuLang.addAction("&%d %s" % (i, lang))
            action.setCheckable(True)
            action.setData(lang)
            if lang == i18n.default_language:
                action.setChecked(True)
            langActionGroup.addAction(action)

    def init_drop(self):
        """Set and activate drag-and-drop functions."""
        self.__class__.dragEnterEvent = self.handleDragEvent
        self.__class__.dragMoveEvent = self.handleDragEvent
        self.__class__.dropEvent = self.handleDropEvent
        self.setAcceptDrops(True)

    def init_app (self, project):
        """Set window size and position, GUI options and reset status."""
        data = self.settings.read_geometry()
        if data["size"] is not None:
            self.resize(data["size"])
        if data["pos"] is not None:
            self.move(data["pos"])
        self.options.set_options(self.settings.read_options())
        self.status = Status.idle
        self.actionSave.setEnabled(False)
        if project:
            loadproject(self, project)
        else:
            msg = self.config_error or _("Ready.")
            self.set_statusmsg(msg)
        data = self.settings.read_misc()
        self.saveresultas = data['saveresultas']

    def get_qhcpath (self):
        """Helper function to search for the QHC help file in different
        locations."""
        devel_dir = os.path.join(configuration.configdata.install_data, "doc", "html")
        return configuration.get_share_file('lccollection.qhc', devel_dir=devel_dir)

    def connect_widgets (self):
        """Connect widget signals. Some signals use the AutoConnect feature.
        Autoconnected methods have the form on_<objectname>_<signal>.
        """
        def set_idle ():
            """Set application status to idle."""
            self.status = Status.idle
            self.set_statusmsg(_("Check finished."))
            self.controlButton.clicked.disconnect(self.checker.cancel)
        self.checker.finished.connect(set_idle)
        self.checker.terminated.connect(set_idle)
        self.log_url_signal.connect(self.model.log_url)
        self.log_stats_signal.connect(self.log_stats)
        self.error_signal.connect(self.internal_error)
        self.options.editor.saved.connect(self.read_config)
        self.log_status_signal.connect(self.log_status)
        self.prop_url.linkHovered.connect(self.hover_link)
        self.prop_parenturl.linkHovered.connect(self.hover_link)

    def init_shortcuts (self):
        """Configure application shortcuts."""
        def selectUrl():
            """Highlight URL input textbox."""
            self.urlinput.setFocus()
            self.urlinput.selectAll()
        shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        shortcut.activated.connect(selectUrl)

    def init_treeview (self):
        """Set treeview model and layout."""
        self.model = UrlItemModel()
        self.treeView.setModel(self.model)
        data = self.settings.read_treeviewcols()
        self.treeView.setColumnWidth(0, data["col1"])
        self.treeView.setColumnWidth(1, data["col2"])
        self.treeView.setColumnWidth(2, data["col3"])
        selectionModel = self.treeView.selectionModel()
        selectionModel.selectionChanged.connect(self.set_properties)

    def get_treeviewcols (self):
        """Return URL treeview column widths."""
        return dict(
            col1=self.treeView.columnWidth(0),
            col2=self.treeView.columnWidth(1),
            col3=self.treeView.columnWidth(2),
        )

    def init_config (self):
        """Create a configuration object."""
        self.config = configuration.Configuration()
        # dictionary holding overwritten values
        self.config_backup = {}
        # set standard GUI configuration values
        self.config.logger_add(SignalLogger)
        self.config["logger"] = self.config.logger_new(SignalLogger.LoggerName,
            signal=self.log_url_signal, stats=self.log_stats_signal)
        self.config["status"] = True
        self.config["status_wait_seconds"] = 2
        self.handler = GuiLogHandler(self.debug.log_msg_signal)
        status = StatusLogger(self.log_status_signal)
        self.config.init_logging(status, handler=self.handler)

    def read_config (self, filename=None):
        """Read user and system configuration file."""
        try:
            self.config.read()
        except LinkCheckerError as msg:
            self.config_error = unicode(msg)

    def set_config (self):
        """Set configuration."""
        data = self.options.get_options()
        self.config["recursionlevel"] = data["recursionlevel"]
        self.config["verbose"] = data["verbose"]
        if data["debug"]:
            self.config.set_debug(["all"])
            # make sure at least one thread is used
            self.config["threads"] = 1
        else:
            self.config.reset_loglevel()
        if data["warninglines"]:
            lines = data["warninglines"].splitlines()
            pattern = warninglines2regex(lines)
            args = dict(warningregex=pattern)
            self.backup_config("enabledplugins", ["RegexCheck"])
            self.config["RegexCheck"] = args
        # set ignore patterns
        ignorepats = data["ignorelines"].strip()
        if ignorepats:
            self.backup_config("externlinks")
            lines = ignorepats.splitlines()
            for line in lines:
                try:
                    pat = get_link_pat(line, strict=1)
                    self.config["externlinks"].append(pat)
                except re.error as err:
                    msg = _("Invalid regular expression %r: %s" % (pat, err))
                    self.set_statusmsg(msg)
        # make sure the configuration is sane
        self.config.sanitize()

    def backup_config (self, key, value=None):
        """Backup config key if not already done and set given value."""
        if key not in self.config_backup:
            confvalue = self.config[key]
            if isinstance(confvalue, list):
                # make copy of lists to avoid unwanted inserted items
                confvalue = confvalue[:]
            self.config_backup[key] = confvalue
        if value is not None:
            self.config[key] = value

    def restore_config (self):
        """Restore config from backup."""
        for key in self.config_backup:
            confvalue = self.config_backup[key]
            if isinstance(confvalue, list):
                # make copy of lists to avoid unwanted inserted items
                confvalue = confvalue[:]
            self.config[key] = confvalue

    def get_status (self):
        """Return current application status."""
        return self._status

    def set_status (self, status):
        """Set application status."""
        self._status = status
        if status == Status.idle:
            self.aggregate = None
            self.controlButton.setText(_("Start"))
            self.controlButton.setIcon(self.icon_start)
            self.controlButton.setEnabled(True)
            self.actionSave.setEnabled(True)
            self.actionDebug.setEnabled(self.options.get_options()["debug"])
            self.treeView.sortByColumn(0, QtCore.Qt.AscendingOrder)
            self.treeView.setSortingEnabled(True)
            self.treeView.scrollToTop()
            self.movie.stop()
            # Reset progress information.
            self.label_active.setText(u"0")
            self.label_queued.setText(u"0")
            self.label_checked.setText(u"0")
            self.label_busy.hide()
            self.menubar.setEnabled(True)
            self.urlinput.setEnabled(True)
            self.restore_config()
        elif status == Status.checking:
            self.treeView.setSortingEnabled(False)
            self.debug.reset()
            self.set_statusmsg(_(u"Checking site..."))
            # disable commands
            self.menubar.setEnabled(False)
            self.urlinput.setEnabled(False)
            # reset widgets
            self.controlButton.setText(_("Stop"))
            self.controlButton.setIcon(self.icon_stop)
            self.controlButton.clicked.connect(self.checker.cancel)
            self.movie.start()
            self.label_busy.show()

    status = property(get_status, set_status)

    @QtCore.pyqtSlot()
    def on_actionHelp_triggered (self):
        """Show help page."""
        url = QtCore.QUrl("%sindex.html" % DocBaseUrl)
        self.assistant.showDocumentation(url)

    @QtCore.pyqtSlot()
    def on_actionOptions_triggered (self):
        """Show option dialog."""
        self.options.exec_()

    @QtCore.pyqtSlot()
    def on_actionQuit_triggered (self):
        """Quit application."""
        self.close()

    def closeEvent (self, e=None):
        """Save settings and remove registered logging handler"""
        self.settings.save_geometry(dict(size=self.size(), pos=self.pos()))
        self.settings.save_treeviewcols(self.get_treeviewcols())
        self.settings.save_options(self.options.get_options())
        self.settings.save_recent_documents(self.recent.get_documents())
        self.settings.save_misc(dict(saveresultas=self.saveresultas))
        self.settings.sync()
        self.config.remove_loghandler(self.handler)
        if e is not None:
            e.accept()

    @QtCore.pyqtSlot()
    def on_actionAbout_triggered (self):
        """Display about dialog."""
        modules = u"<br>\n".join(configuration.get_modules_info())
        d = {
            "app": configuration.App,
            "appname": configuration.AppName,
            "copyright": configuration.HtmlCopyright,
            "donateurl": configuration.DonateUrl,
            "pyver": u"%d.%d.%d" % sys.version_info[:3],
            "modules": modules,
            "portable": _("yes") if configuration.Portable else _("no"),
            "releasedate": configuration.ReleaseDate,
        }
        QtGui.QMessageBox.about(self, _(u"About %(appname)s") % d,
            _(u"""<qt><center>
<h1>%(app)s</h1>
<p>Released on %(releasedate)s
<p>Python: %(pyver)s<br>
%(modules)s<br>
Portable version: %(portable)s
<p>%(copyright)s
<br>%(appname)s is licensed under the
<a href="http://www.gnu.org/licenses/gpl.html">GPL</a>
Version 2 or later.
<p>If you like %(appname)s, consider one of several ways to
<a href="%(donateurl)s">donate</a>. Thanks!
</center></qt>""") % d)

    @QtCore.pyqtSlot()
    def on_actionDebug_triggered (self):
        """Display debug dialog."""
        self.debug.show()

    @QtCore.pyqtSlot()
    def on_actionOpen_project_triggered (self):
        """Open project."""
        openproject(self)

    @QtCore.pyqtSlot()
    def on_actionSave_project_triggered (self):
        """Save project."""
        saveproject(self, self.get_url())

    @QtCore.pyqtSlot()
    def on_actionSave_triggered (self):
        """Save URL results."""
        saveresultas = urlsave(self, self.config, self.model.urls)
        if saveresultas:
            self.saveresultas = saveresultas

    @QtCore.pyqtSlot()
    def on_actionCheckUpdates_triggered (self):
        """Display update check result."""
        dialog = UpdateDialog(self)
        dialog.reset()
        dialog.show()

    def start (self):
        """Start a new check."""
        if self.status == Status.idle:
            self.check()

    on_urlinput_returnPressed = start

    def cancel (self):
        """Note that checking is canceled."""
        self.controlButton.setEnabled(False)
        duration = strformat.strduration_long(self.config["aborttimeout"])
        self.set_statusmsg(_(u"Closing active URLs with timeout %s...") % duration)

    @QtCore.pyqtSlot()
    def on_controlButton_clicked (self):
        """Start or Cancel has been clicked."""
        if self.status == Status.idle:
            self.start()
        elif self.status == Status.checking:
            self.cancel()
        else:
            raise ValueError("Invalid application status %r" % self.status)

    def get_url (self):
        """Return URL to check from the urlinput widget."""
        url = strformat.stripurl(unicode(self.urlinput.text()))
        url = checker.guess_url(url)
        if url and u":" not in url:
            # Look for local file, else assume it's an HTTP URL.
            if not os.path.exists(url):
                url = u"http://%s" % url
        return url

    def check (self):
        """Check given URL."""
        self.model.clear()
        clear_properties(self)
        clear_statistics(self)
        self.set_config()
        aggregate = director.get_aggregate(self.config)
        url = self.get_url()
        if not url:
            self.set_statusmsg(_("Error, empty URL"))
            return
        self.set_statusmsg(_("Checking '%s'.") % strformat.limit(url, 40))
        url_data = checker.get_url_from(url, 0, aggregate, extern=(0, 0))
        self.recent.add_document(url)
        aggregate.urlqueue.put(url_data)
        self.aggregate = aggregate
        # check in background
        self.checker.check(self.aggregate)
        self.status = Status.checking

    def set_properties (self, selected, deselected):
        """Set URL properties for selected item."""
        indexes = selected.indexes()
        if len(indexes):
            index = indexes[0]
            urlitem = self.model.getUrlItem(index)
            if urlitem is not None:
                set_properties(self, urlitem.url_data)
        selected_rows = len(self.treeView.selectionModel().selectedRows())
        if selected_rows:
            self.set_statusmsg(_n("%d URL selected.", "%d URLs selected",
                               selected_rows) % selected_rows)
        else:
            self.set_statusmsg(_("Ready."))

    def on_treeView_customContextMenuRequested (self, point):
        """Show item context menu."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            self.contextmenu.enableFromItem(urlitem)
            self.contextmenu.popup(QtGui.QCursor.pos())

    @QtCore.pyqtSlot()
    def on_actionViewOnline_triggered (self):
        """View item URL online."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            webbrowser.open(urlitem.url_data.url)

    @QtCore.pyqtSlot()
    def on_actionViewParentOnline_triggered (self):
        """View item parent URL online."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            webbrowser.open(urlitem.url_data.parent_url)

    @QtCore.pyqtSlot()
    def on_actionViewParentSource_triggered (self):
        """View item parent URL source in local text editor (read-only)."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem is not None:
            self.view_source(urlitem.url_data.parent_url,
                             urlitem.url_data.line, urlitem.url_data.column)

    def view_source (self, url, line, col):
        """View URL source in editor window."""
        self.editor.setWindowTitle(u"View %s" % url)
        self.editor.setUrl(url)
        data, info = urlutil.get_content(url, proxy=self.config["proxy"])
        if data is None:
            msg = u"An error occurred retreiving URL `%s': %s." % (url, info)
            self.editor.setText(msg)
        else:
            content_type = httputil.get_content_type(info)
            if not content_type:
                # read function for content type guessing
                read = lambda: data
                content_type = fileutil.guess_mimetype(url, read=read)
            self.editor.setContentType(content_type)
            self.editor.setText(data, line=line, col=col)
        self.editor.show()

    @QtCore.pyqtSlot()
    def on_actionCopyToClipboard_triggered (self):
        """Copy item URL to clipboard."""
        urlitem = self.model.getUrlItem(self.treeView.currentIndex())
        if urlitem:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(urlitem.url_data.url)
            event = QtCore.QEvent(QtCore.QEvent.Clipboard)
            QtGui.QApplication.sendEvent(clipboard, event)

    def set_statusmsg (self, msg):
        """Show given status message."""
        self.statusBar.showMessage(msg)
        if len(msg) > MaxMessageLength:
            self.label_status.setToolTip(msg)
            msg = msg[:MaxMessageLength-3]+u"..."
        else:
            self.label_status.setToolTip(u"")
        self.label_status.setText(msg)

    def hover_link (self, link):
        """Show given link in status bar."""
        self.statusBar.showMessage(link)

    def log_status (self, checked, in_progress, queued, duration, num_urls):
        """Update number of checked, active and queued links."""
        self.label_checked.setText(u"%d" % checked)
        self.label_active.setText(u"%d" % in_progress)
        self.label_queued.setText(u"%d" % queued)

    def log_stats (self, statistics):
        """Set statistic information for selected URL."""
        set_statistics(self, statistics)

    def internal_error (self, msg):
        """Display internal error message. Triggered by sys.excepthook()."""
        QtGui.QMessageBox.warning(self, _(u"LinkChecker internal error"), msg)

    def handleDragEvent(self, event):
        """Handle drag enter of move event."""
        mime = event.mimeData()
        if not mime.hasUrls():
            return event.ignore()
        url = mime.urls()[0]
        if url.scheme() != 'file':
            return event.ignore()
        event.accept()

    def handleDropEvent(self, event):
        """Handle drop event. Detects and loads project files, else sets the URL."""
        mime = event.mimeData()
        url = mime.urls()[0]
        if url.path().toLower().endsWith(ProjectExt):
            filename = unicode(url.toLocalFile())
            loadproject(self, filename)
        else:
            self.urlinput.setText(url.toString())

    def retranslateUi(self, Window):
        """Translate menu titles."""
        super(LinkCheckerMain, self).retranslateUi(Window)
        # self.menu_lang is created after calling retranslateUi
        # the first time, so check for its excistance
        if hasattr(self, "menu_lang"):
            self.menuLang.setTitle(_("&Language"))

    def switch_language(self, action):
        """Change UI language."""
        lang = str(action.data().toString())
        i18n.install_language(lang)
        self.retranslateUi(self)
        self.options.retranslateUi(self.options)
        self.debug.retranslateUi(self.debug)
        self.editor.retranslateUi(self.editor)
