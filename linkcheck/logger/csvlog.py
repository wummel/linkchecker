# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
"""
A CSV logger.
"""

import time
import csv
import os

import linkcheck.logger
import linkcheck.configuration


class CSVLogger (linkcheck.logger.Logger):
    """
    CSV output, consisting of one line per entry. Entries are
    separated by a semicolon.
    """

    def __init__ (self, **args):
        """
        Store default separator and (os dependent) line terminator.
        """
        super(CSVLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.separator = args['separator']
        self.quotechar = args['quotechar']

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
        if self.fd is None:
            return
        self.starttime = time.time()
        row = []
        if self.has_part("intro"):
            self.comment(_("created by %s at %s") %
                         (linkcheck.configuration.AppName,
                          linkcheck.strformat.strtime(self.starttime)))
            self.comment(_("Get the newest version at %(url)s") %
                         {'url': linkcheck.configuration.Url})
            self.comment(_("Write comments and bugs to %(email)s") %
                         {'email': linkcheck.configuration.Email})
            self.check_date()
            self.comment(_("Format of the entries:"))
            for s in (u"urlname",
                      u"recursionlevel",
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
                self.comment(s)
                row.append(s)
            self.flush()
        self.writer = csv.writer(self.fd, dialect='excel',
                        delimiter=self.separator, lineterminator=os.linesep,
                        quotechar=self.quotechar)
        if row:
            self.writer.writerow(row)

    def log_url (self, url_data):
        """
        Write csv formatted url check info.
        """
        if self.fd is None:
            return
        row = []
        for s in [url_data.base_url or u"", url_data.recursion_level,
               url_data.parent_url or u"", url_data.base_ref or u"",
               url_data.result,
               os.linesep.join([x[1] for x in url_data.warnings]),
               os.linesep.join([x[1] for x in url_data.info]),
               url_data.valid, url_data.url or u"",
               url_data.line, url_data.column,
               url_data.name, url_data.dltime,
               url_data.dlsize, url_data.checktime,
               url_data.cached]:
            if isinstance(s, unicode):
                row.append(s.encode(self.output_encoding, "ignore"))
            else:
                row.append(s)
        self.writer.writerow(row)
        self.flush()

    def end_output (self):
        """
        Write end of checking info as csv comment.
        """
        if self.fd is None:
            return
        self.stoptime = time.time()
        if self.has_part("outro"):
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %s (%s)") %
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration_long(duration)))
        self.close_fileoutput()
