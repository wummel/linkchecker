# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2011 Bastian Kleineidam
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
from PyQt4 import QtGui

LoggerFilters = ";;".join((
    _("HTML output (*.html)"),
    _("Text output (*.txt)"),
    _("XML output (*.xml)"),
    _("CSV output (*.csv)"),
))

FileExt2LogType = {
    ".html": "html",
    ".txt": "text",
    ".xml": "xml",
    ".csv": "csv",
}

def urlsave (parent, config, urls):
    """Save URL results in file."""
    res = get_save_filename(parent)
    if not res:
        # user canceled
        return
    filename = unicode(res)
    logtype = FileExt2LogType.get(os.path.splitext(filename)[1])
    if not logtype:
        return
    kwargs = dict(fileoutput=1, filename=filename, encoding="utf_8_sig")
    logger = config.logger_new(logtype, **kwargs)
    logger.start_output()
    for urlitem in urls:
        logger.log_url(urlitem.url_data)
    logger.end_output()


def get_save_filename (parent):
    """Open file save dialog for given parent window and base directory.
    Return dialog result."""
    filename = "linkchecker-out.html"
    title = _("Save check results")
    func = QtGui.QFileDialog.getSaveFileName
    return func(parent, title, filename, LoggerFilters)
