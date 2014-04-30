# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
"""
A CSV logger.
"""
import csv
import os
from cStringIO import StringIO
from . import _Logger
from .. import strformat

Columns = (
    u"urlname", u"parentname", u"baseref", u"result", u"warningstring",
    u"infostring", u"valid", u"url", u"line", u"column", u"name",
    u"dltime", u"size", u"checktime", u"cached", u"level", u"modified",
)


class CSVLogger (_Logger):
    """
    CSV output, consisting of one line per entry. Entries are
    separated by a separator (a semicolon per default).
    """

    LoggerName = "csv"

    LoggerArgs = {
        "filename": "linkchecker-out.csv",
        'separator': ';',
        "quotechar": '"',
        "dialect": "excel",
    }

    def __init__ (self, **kwargs):
        """Store default separator and (os dependent) line terminator."""
        args = self.get_args(kwargs)
        super(CSVLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.separator = args['separator']
        self.quotechar = args['quotechar']
        self.dialect = args['dialect']
        self.linesep = os.linesep

    def comment (self, s, **args):
        """Write CSV comment."""
        self.writeln(s=u"# %s" % s, **args)

    def start_output (self):
        """Write checking start info as csv comment."""
        super(CSVLogger, self).start_output()
        row = []
        if self.has_part("intro"):
            self.write_intro()
            self.flush()
        else:
            # write empty string to initialize file output
            self.write(u"")
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=self.dialect,
               delimiter=self.separator, lineterminator=self.linesep,
               quotechar=self.quotechar)
        for s in Columns:
            if self.has_part(s):
                row.append(s)
        if row:
            self.writerow(row)

    def log_url (self, url_data):
        """Write csv formatted url check info."""
        row = []
        if self.has_part("urlname"):
            row.append(url_data.base_url)
        if self.has_part("parentname"):
            row.append(url_data.parent_url)
        if self.has_part("baseref"):
            row.append(url_data.base_ref)
        if self.has_part("result"):
            row.append(url_data.result)
        if self.has_part("warningstring"):
            row.append(self.linesep.join(x[1] for x in url_data.warnings))
        if self.has_part("infostring"):
            row.append(self.linesep.join(url_data.info))
        if self.has_part("valid"):
            row.append(url_data.valid)
        if self.has_part("url"):
            row.append(url_data.url)
        if self.has_part("line"):
            row.append(url_data.line)
        if self.has_part("column"):
            row.append(url_data.column)
        if self.has_part("name"):
            row.append(url_data.name)
        if self.has_part("dltime"):
            row.append(url_data.dltime)
        if self.has_part("dlsize"):
            row.append(url_data.size)
        if self.has_part("checktime"):
            row.append(url_data.checktime)
        if self.has_part("cached"):
            row.append(0)
        if self.has_part("level"):
            row.append(url_data.level)
        if self.has_part("modified"):
            row.append(self.format_modified(url_data.modified))
        self.writerow(map(strformat.unicode_safe, row))
        self.flush()

    def writerow (self, row):
        """Write one row in CSV format."""
        self.writer.writerow([s.encode("utf-8", self.codec_errors) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and write to the target stream
        self.write(data)
        # empty queue
        self.queue.truncate(0)

    def end_output (self, **kwargs):
        """Write end of checking info as csv comment."""
        if self.has_part("outro"):
            self.write_outro()
        self.close_fileoutput()
