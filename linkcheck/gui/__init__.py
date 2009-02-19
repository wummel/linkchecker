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

import os
from PyQt4 import QtCore, QtGui, QtHelp
from .linkchecker_ui_main import Ui_MainWindow
from .linkchecker_ui_options import Ui_Options
from .linkchecker_ui_progress import Ui_ProgressDialog
from .. import configuration, checker, director, add_intern_pattern, \
    strformat
from ..containers import enum

DocBaseUrl = "qthelp://bfk.app.linkchecker/doc/build/htmlhelp/"

Status = enum('idle', 'checking')


def set_fixed_font (output):
    """Set fixed font on output widget."""
    if os.name == 'nt':
        output.setFontFamily("Courier")
    else:
        output.setFontFamily("mono")


class LinkCheckerMain (QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None, url=None):
        """Initialize UI."""
        super(LinkCheckerMain, self).__init__(parent)
        self.setupUi(self)
        if url:
            self.urlinput.setText(url)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(configuration.App)
        self.options = LinkCheckerOptions(parent=self)
        self.progress = LinkCheckerProgress(parent=self)
        set_fixed_font(self.output)
        self.checker = Checker()
        settings = QtCore.QSettings('bfk', configuration.AppName)
        settings.beginGroup('mainwindow')
        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
            self.move(settings.value('pos').toPoint())
        settings.endGroup()
        # Note: we can't use QT assistant here because of the .exe packaging
        self.assistant = HelpWindow(self, "doc/lccollection.qhc")
        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("add_message(QString)"), self.add_message)
        self.connect(self.checker, QtCore.SIGNAL("log_url(PyQt_PyObject)"), self.log_url)
        self.connect(self.checker, QtCore.SIGNAL("status(QString)"), self.progress.status)
        self.connect(self.controlButton, QtCore.SIGNAL("clicked()"), self.start)
        self.connect(self.optionsButton, QtCore.SIGNAL("clicked()"), self.options.exec_)
        self.connect(self.actionQuit, QtCore.SIGNAL("triggered()"), self.close)
        self.connect(self.actionAbout, QtCore.SIGNAL("triggered()"), self.about)
        self.connect(self.actionHelp, QtCore.SIGNAL("triggered()"), self.showDocumentation)
        self.status = Status.idle
        #self.controlButton.setText(_("Start"))
        #icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap(":/icons/start.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #self.controlButton.setIcon(icon)

    def get_status (self):
        return self._status

    def set_status (self, status):
        self._status = status
        if status == Status.idle:
            self.progress.reset()
            self.progress.hide()
            self.aggregate = None
            self.controlButton.setEnabled(True)
            self.optionsButton.setEnabled(True)
            self.set_statusbar(_("Ready."))
        elif status == Status.checking:
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
        self.output.setText("")
        config = self.get_config()
        aggregate = director.get_aggregate(config)
        url = unicode(self.urlinput.text()).strip()
        if not url:
            self.output.setText(_("Error, empty URL"))
            self.status = Status.idle
            return
        if url.startswith(u"www."):
            url = u"http://%s" % url
        elif url.startswith(u"ftp."):
            url = u"ftp://%s" % url
        self.set_statusbar(_("Checking '%s'.") % strformat.limit(url, 40))
        url_data = checker.get_url_from(url, 0, aggregate)
        try:
            add_intern_pattern(url_data, config)
        except UnicodeError:
            self.output.setText(_("Error, invalid URL '%s'.") %
                                  strformat.limit(url, 40))
            self.status = Status.idle
            return
        aggregate.urlqueue.put(url_data)
        self.aggregate = aggregate
        # check in background
        self.progress.show()
        self.checker.check(self.aggregate, self.progress)
        self.status = Status.checking

    def get_config (self):
        """Return check configuration."""
        config = configuration.Configuration()
        config["recursionlevel"] = self.options.recursionlevel.value()
        config.logger_add("gui", GuiLogger)
        config["logger"] = config.logger_new('gui', widget=self.checker)
        config["verbose"] = self.options.verbose.isChecked()
        config["timeout"] = self.options.timeout.value()
        config["threads"] = self.options.threads.value()
        config.init_logging(StatusLogger(self.checker))
        config["status"] = True
        return config

    def add_message (self, msg):
        """Add new log message to text edit widget."""
        text = self.output.toPlainText()
        self.output.setText(text+msg)
        self.output.moveCursor(QtGui.QTextCursor.End)

    def log_url (self, url_data):
        pass # XXX log url_data

    def set_statusbar (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)


class HelpWindow (QtGui.QDialog):
    """A custom help display dialog."""

    def __init__ (self, parent, qhcpath):
        """Initialize dialog and load qhc help project from given path."""
        super(HelpWindow, self).__init__(parent)
        self.engine = QtHelp.QHelpEngine(qhcpath, self)
        self.engine.setupData()
        self.setWindowTitle(u"%s Help" % configuration.AppName)
        self.build_ui()

    def build_ui (self):
        """Build UI for the help window."""
        splitter = QtGui.QSplitter()
        splitter.setOrientation(QtCore.Qt.Vertical)
        self.browser = HelpBrowser(splitter, self.engine)
        tree = self.engine.contentWidget()
        tree.setExpandsOnDoubleClick(False)
        splitter.addWidget(tree)
        splitter.addWidget(self.browser)
        splitter.setSizes((70, 530))
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(splitter)
        self.setLayout(hlayout)
        self.resize(800, 600)
        self.connect(self.engine.contentWidget(),
            QtCore.SIGNAL("linkActivated(QUrl)"),
            self.browser, QtCore.SLOT("setSource(QUrl)"))

    def showDocumentation (self, url):
        """Show given URL in help browser."""
        self.browser.setSource(url)
        self.show()


class HelpBrowser (QtGui.QTextBrowser):
    """A QTextBrowser that can handle qthelp:// URLs."""

    def __init__ (self, parent, engine):
        """Initialize and store given HelpEngine instance."""
        super(HelpBrowser, self).__init__(parent)
        self.engine = engine

    def setSource (self, url):
        if url.scheme() == "http":
            import webbrowser
            webbrowser.open(str(url.toString()))
        else:
            QtGui.QTextBrowser.setSource(self, url)

    def loadResource (self, rtype, url):
        """Handle qthelp:// URLs, load content from help engine."""
        if url.scheme() == "qthelp":
            return QtCore.QVariant(self.engine.fileData(url))
        return QtGui.QTextBrowser.loadResource(self, rtype, url)


class LinkCheckerOptions (QtGui.QDialog, Ui_Options):
    """Hold options for current URL to check."""

    def __init__ (self, parent=None):
        super(LinkCheckerOptions, self).__init__(parent)
        self.setupUi(self)
        self.connect(self.resetButton, QtCore.SIGNAL("clicked()"), self.reset)
        self.connect(self.closeButton, QtCore.SIGNAL("clicked()"), self.close)

    def reset (self):
        """Reset options to default values."""
        self.recursionlevel.setValue(-1)
        self.verbose.setChecked(False)
        self.threads.setValue(10)
        self.timeout.setValue(60)


class LinkCheckerProgress (QtGui.QDialog, Ui_ProgressDialog):
    """Show progress bar."""

    def __init__ (self, parent=None):
        super(LinkCheckerProgress, self).__init__(parent)
        self.setupUi(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        set_fixed_font(self.textBrowser)

    def status (self, msg):
        text = self.textBrowser.toPlainText()
        self.textBrowser.setText(text+msg)
        self.textBrowser.moveCursor(QtGui.QTextCursor.End)

    def reset (self):
        self.textBrowser.setText(u"")


class Checker (QtCore.QThread):
    """Separate checker thread."""

    def __init__ (self, parent=None):
        super(Checker, self).__init__(parent)
        self.exiting = False
        self.aggregate = None
        self.progress = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def check (self, aggregate, progress):
        self.aggregate = aggregate
        self.progress = progress
        self.connect(self.progress.cancelButton, QtCore.SIGNAL("clicked()"), self.cancel)
        # setup the thread and call run()
        self.start()

    def cancel (self):
        # stop checking
        if self.progress is not None:
            self.progress.cancelButton.setEnabled(False)
            self.progress = None
        if self.aggregate is not None:
            self.aggregate.wanted_stop = True
            self.aggregate = None

    def run (self):
        # start checking
        director.check_urls(self.aggregate)


from linkcheck.logger.text import TextLogger

class GuiLogger (TextLogger):
    """Custom logger class to delegate log messages to the UI."""

    def __init__ (self, **args):
        super(GuiLogger, self).__init__(**args)
        self.widget = args["widget"]
        self.end_output_called = False

    def write (self, s, **args):
        self.widget.emit(QtCore.SIGNAL("add_message(QString)"), s)

    def start_fileoutput (self):
        pass

    def close_fileoutput (self):
        pass

    def end_output (self):
        # The linkchecker director thread is not the main thread, and
        # it can call end_output() twice, from director.check_urls() and
        # from director.abort(). This happends when LinkCheckerMain.stop()
        # is called. The flag prevents double printing of the output.
        if not self.end_output_called:
            self.end_output_called = True
            super(GuiLogger, self).end_output()

    def log_url (self, url_data):
        super(GuiLogger, self).log_url(url_data)
        self.widget.emit(QtCore.SIGNAL("log_url(PyQt_PyObject)"), url_data)


class StatusLogger (object):
    """Custom status logger to delegate status message to the UI."""

    def __init__ (self, widget):
        self.widget = widget
        self.buf = []

    def write (self, msg):
        self.buf.append(msg)

    def writeln (self, msg):
        self.buf.extend([msg, unicode(os.linesep)])

    def flush (self):
        self.widget.emit(QtCore.SIGNAL("status(QString)"), u"".join(self.buf))
        self.buf = []
