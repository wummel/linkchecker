# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
from PyQt4 import QtGui, QtCore

FilterHtml = _("HTML output (*.html)")
FilterText = _("Text output (*.txt)")
FilterXml = _("XML output (*.xml)")
FilterCsv = _("CSV output (*.csv)")

LoggerFilters = (
    FilterHtml,
    FilterText,
    FilterXml,
    FilterCsv,
)

Logtype2Filter = {
    'html': FilterHtml,
    'text': FilterText,
    'xml': FilterXml,
    'csv': FilterCsv,
}
Filter2Logtype = {v: k for k, v in Logtype2Filter.items()}

Logtype2FileExt = {
    "html": ".html",
    "text": ".txt",
    "xml": ".xml",
    "csv": ".csv",
}

def urlsave (parent, config, urls):
    """Save URL results in file."""
    filename, logtype = get_save_filename(parent)
    if not filename:
        # user canceled
        return
    filename = unicode(filename)
    kwargs = dict(fileoutput=1, filename=filename, encoding="utf_8_sig")
    logger = config.logger_new(logtype, **kwargs)
    logger.start_output()
    for urlitem in urls:
        do_print = True
        logger.log_filter_url(urlitem.url_data, do_print)
    # inject the saved statistics before printing them
    logger.stats = config['logger'].stats
    logger.end_output()
    return logtype


def get_save_filename (parent):
    """Open file save dialog for given parent window and base directory.
    Return dialog result."""
    title = _("Save check results")
    func = QtGui.QFileDialog.getSaveFileName
    logtype = parent.saveresultas if parent.saveresultas else 'html'
    filters = ";;".join(sortwithfirst(LoggerFilters, Logtype2Filter[logtype]))
    filename = "linkchecker-out" + Logtype2FileExt[logtype]
    selectedFilter = QtCore.QString()
    res = func(parent, title, filename, filters, selectedFilter)
    logtype = Filter2Logtype.get(unicode(selectedFilter))
    return res, logtype


def sortwithfirst(sequence, firstelement):
    """Move firstelement in a sequence to the first position."""
    res = []
    for elem in sequence:
        if elem == firstelement:
            res.insert(0, elem)
        else:
            res.append(elem)
    return res
