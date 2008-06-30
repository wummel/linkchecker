# -*- coding: iso-8859-1 -*-
# Copyright (C) 2008 Bastian Kleineidam
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
from linkchecker_ui import Ui_MainWindow
import linkcheck
from linkcheck import configuration, checker, director, add_intern_pattern, \
    strformat


class LinkCheckerMain (QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        """Initialize UI."""
        super(LinkCheckerMain, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(configuration.App)
        self.textEdit.setFontFamily("mono")
        self.checker = Checker()

        settings = QtCore.QSettings('bfk', configuration.AppName)
        settings.beginGroup('mainwindow')

        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
            self.move(settings.value('pos').toPoint())
        settings.endGroup()

        self.connect(self.checker, QtCore.SIGNAL("finished()"), self.updateUi)
        self.connect(self.checker, QtCore.SIGNAL("terminated()"), self.updateUi)
        self.connect(self.checker, QtCore.SIGNAL("addMessage(QString)"), self.addMessage)
        self.connect(self.checker, QtCore.SIGNAL("setStatus(QString)"), self.setStatus)
        self.connect(self.pushButton, QtCore.SIGNAL("clicked()"), self.check_or_cancel)
        self.connect(self.actionQuit, QtCore.SIGNAL("triggered()"), self.close)
        self.connect(self.actionAbout, QtCore.SIGNAL("triggered()"), self.about)
        self.updateUi()

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

    def check_or_cancel (self):
        """Run a new check or cancel active check."""
        if self.aggregate is None:
            self.check()
        else:
            self.cancel()

    def check (self):
        """Check given URL."""
        self.pushButton.setEnabled(False)
        self.textEdit.setText("")
        config = self.get_config()
        aggregate = director.get_aggregate(config)
        url = unicode(self.lineEdit.text()).strip()
        if not url:
            self.textEdit.setText(_("Error, empty URL"))
            self.updateUi()
            return
        if url.startswith(u"www."):
            url = u"http://%s" % url
        elif url.startswith(u"ftp."):
            url = u"ftp://%s" % url
        self.setStatus(_("Checking '%s'.") % strformat.limit(url, 40))
        url_data = checker.get_url_from(url, 0, aggregate)
        try:
            add_intern_pattern(url_data, config)
        except UnicodeError:
            self.textEdit.setText(_("Error, invalid URL '%s'.") %
                                  strformat.limit(url, 40))
            self.updateUi()
            return
        aggregate.urlqueue.put(url_data)
        self.pushButton.setText(_("Cancel"))
        self.aggregate = aggregate
        self.pushButton.setEnabled(True)
        # check in background
        self.checker.check(self.aggregate)

    def cancel (self):
        """Cancel running check."""
        self.setStatus(_("Aborting."))
        director.abort(self.aggregate)

    def get_config (self):
        """Return check configuration."""
        config = configuration.Configuration()
        config["recursionlevel"] = self.spinBox.value()
        config.logger_add("gui", GuiLogger)
        config["logger"] = config.logger_new('gui', widget=self.checker)
        config["verbose"] = self.checkBox.isChecked()
        config.init_logging(StatusLogger(self.checker))
        config["status"] = True
        return config

    def addMessage (self, msg):
        """Add new log message to text edit widget."""
        text = self.textEdit.toPlainText()
        self.textEdit.setText(text+msg)
        self.textEdit.moveCursor(QtGui.QTextCursor.End)

    def setStatus (self, msg):
        """Show status message in status bar."""
        self.statusBar.showMessage(msg)

    def updateUi (self):
        """Reset UI."""
        self.pushButton.setText(_("Check"))
        self.aggregate = None
        self.pushButton.setEnabled(True)
        self.setStatus(_("Ready."))


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

    def write (self, s, **args):
        self.widget.emit(QtCore.SIGNAL("addMessage(QString)"), s)

    def start_fileoutput (self):
        pass

    def close_fileoutput (self):
        pass


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
        self.widget.emit(QtCore.SIGNAL("setStatus(QString)"), u"".join(self.buf))
        self.buf = []
