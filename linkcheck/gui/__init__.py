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
from PyQt4 import QtCore, QtGui
from .linkchecker_ui_main import Ui_MainWindow
from .linkchecker_ui_options import Ui_Options
from .. import configuration, checker, director, add_intern_pattern, \
    strformat
from ..containers import enum


Status = enum('idle', 'checking', 'stopping')

class LinkCheckerMain (QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        """Initialize UI."""
        super(LinkCheckerMain, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(configuration.App)
        self.options = LinkCheckerOptions(parent=self)
        if os.name == 'nt':
            self.output.setFontFamily("Courier")
        else:
            self.output.setFontFamily("mono")
        self.checker = Checker()

        settings = QtCore.QSettings('bfk', configuration.AppName)
        settings.beginGroup('mainwindow')

        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
            self.move(settings.value('pos').toPoint())
        settings.endGroup()

        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.set_status_idle)
        self.connect(self.checker, QtCore.SIGNAL("add_message(QString)"), self.add_message)
        self.connect(self.checker, QtCore.SIGNAL("set_statusbar(QString)"), self.set_statusbar)
        self.connect(self.controlButton, QtCore.SIGNAL("clicked()"), self.start_stop)
        self.connect(self.optionsButton, QtCore.SIGNAL("clicked()"), self.options.exec_)
        self.connect(self.actionQuit, QtCore.SIGNAL("triggered()"), self.close)
        self.connect(self.actionAbout, QtCore.SIGNAL("triggered()"), self.about)
        self.status = Status.idle

    def get_status (self):
        return self._status

    def set_status (self, status):
        self._status = status
        if status == Status.idle:
            self.controlButton.setText(_("Start"))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/icons/start.png"),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            self.controlButton.setIcon(icon)
            self.aggregate = None
            self.controlButton.setEnabled(True)
            self.optionsButton.setEnabled(True)
            self.set_statusbar(_("Ready."))
        elif status == Status.checking:
            self.controlButton.setText(_("Stop"))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/icons/stop.png"),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            self.controlButton.setIcon(icon)
            self.controlButton.setEnabled(True)
            self.optionsButton.setEnabled(False)
        elif status == Status.stopping:
            self.controlButton.setText(_("Start"))
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/icons/start.png"),QtGui.QIcon.Normal,QtGui.QIcon.Off)
            self.controlButton.setIcon(icon)
            self.controlButton.setEnabled(False)
            self.set_statusbar(_("Stopping."))

    status = property(get_status, set_status)

    def set_status_idle (self):
        """Set idle status. Helper function for signal connections."""
        self.status = Status.idle

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

    def start_stop (self):
        """Start a new check or stop an active check."""
        if self.status == Status.idle:
            self.check()
        elif self.status == Status.checking:
            self.stop()

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
        self.checker.check(self.aggregate)
        self.status = Status.checking

    def stop (self):
        director.abort(self.aggregate)
        self.status = Status.stopping

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

    def set_statusbar (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)


class LinkCheckerOptions (QtGui.QDialog, Ui_Options):
    """Hold options for current URL to check."""

    def __init__ (self, parent=None):
        super(LinkCheckerOptions, self).__init__(parent)
        self.setupUi(self)
        self.connect(self.resetButton, QtCore.SIGNAL("clicked()"), self.reset)

    def reset (self):
        """Reset options to default values."""
        self.recursionlevel.setValue(-1)
        self.verbose.setChecked(False)
        self.threads.setValue(10)
        self.timeout.setValue(60)


class Checker (QtCore.QThread):
    """Separate checker thread."""

    def __init__ (self, parent=None):
        super(Checker, self).__init__(parent)
        self.exiting = False
        self.aggregate = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def check (self, aggregate):
        self.aggregate = aggregate
        # setup the thread and call run()
        self.start()

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
        self.widget.emit(QtCore.SIGNAL("set_statusbar(QString)"), u"".join(self.buf))
        self.buf = []
