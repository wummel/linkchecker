# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2010 Bastian Kleineidam
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
from . import Logger
from .. import strformat


class CSVLogger (Logger):
    """
    CSV output, consisting of one line per entry. Entries are
    separated by a separator (a semicolon per default).
    """

    def __init__ (self, **args):
        """
        Store default separator and (os dependent) line terminator.
        """
        super(CSVLogger, self).__init__(**args)
        # due to a limitation of the csv module, all output has to be
        # utf-8 encoded
        self.output_encoding = "utf-8"
        self.init_fileoutput(args)
        self.separator = args['separator']
        self.quotechar = args['quotechar']
        self.linesep = os.linesep

    def create_fd (self):
        """Create open file descriptor."""
        return open(self.filename, "wb")

    def comment (self, s, **args):
        """
        Write CSV comment.
        """
        self.write(u"# ")
        self.writeln(s=s, **args)

    def start_output (self):
        """
        Write checking start info as csv comment.
        """
        super(CSVLogger, self).start_output()
        row = []
        if self.has_part("intro"):
            self.write_intro()
            self.flush()
        else:
            # write empty string to initialize file output
            self.write(u"")
        self.writer = csv.writer(self.fd, dialect='excel',
               delimiter=self.separator, lineterminator=self.linesep,
               quotechar=self.quotechar)
        for s in (u"urlname",
                  u"parentname",
                  u"baseref",
                  u"result",
                  u"warningstring",
                  u"infostring",
                  u"valid",
                  u"url",
                  u"line",
                  u"column",
                  u"name",
                  u"dltime",
                  u"dlsize",
                  u"checktime",
                  u"cached"):
            if self.has_part(s):
                row.append(s)
        if row:
            self.writerow(row)

    def log_url (self, url_data):
        """
        Write csv formatted url check info.
        """
        row = []
        for s in (url_data.base_url,
               url_data.parent_url, url_data.base_ref,
               url_data.result,
               self.linesep.join(url_data.warnings),
               self.linesep.join(url_data.info),
               url_data.valid, url_data.url,
               url_data.line, url_data.column,
               url_data.name, url_data.dltime,
               url_data.dlsize, url_data.checktime,
               url_data.cached):
            row.append(strformat.unicode_safe(s))
        self.writerow(row)
        self.flush()

    def writerow (self, row):
        self.writer.writerow([self.encode(s) for s in row])

    def encode (self, s):
        return s.encode(self.output_encoding, self.codec_errors)

    def end_output (self):
        """
        Write end of checking info as csv comment.
        """
        if self.has_part("outro"):
            self.write_outro()
        self.close_fileoutput()
