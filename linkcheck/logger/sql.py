# -*- coding: iso-8859-1 -*-
"""an sql logger"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import time
import os

import linkcheck
import linkcheck.logger

from linkcheck.i18n import _


def sqlify (s):
    """escape special SQL chars and strings"""
    if not s:
        return "NULL"
    return "'%s'" % s.replace("'", "''")

def intify (s):
    if not s:
        return 0
    return 1

class SQLLogger (linkcheck.logger.Logger):
    """SQL output for PostgreSQL, not tested"""

    def __init__ (self, **args):
        """initialize database access data"""
        super(SQLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.dbname = args['dbname']
        self.separator = args['separator']

    def start_output (self):
        """print start of checking info as sql comment"""
        linkcheck.logger.Logger.start_output(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field("intro"):
            self.fd.write("-- "+(_("created by %s at %s") % \
                      (linkcheck.configuration.AppName,
                       linkcheck.strformat.strtime(self.starttime))))
            self.fd.write(os.linesep)
            self.fd.write("-- "+(_("Get the newest version at %s") % \
                          linkcheck.configuration.Url))
            self.fd.write(os.linesep)
            self.fd.write("-- "+(_("Write comments and bugs to %s") % \
                          linkcheck.configuration.Email))
            self.fd.write(os.linesep)
            self.fd.write(os.linesep)
            self.flush()

    def new_url (self, url_data):
        """store url check info into the database"""
        if self.fd is None:
            return
        self.fd.write("insert into %(table)s(urlname,recursionlevel,"
              "parentname,baseref,valid,result,warning,info,url,line,col,"
              "name,checktime,dltime,dlsize,cached) values ("
              "%(base_url)s,"
              "%(recursion_level)d,"
              "%(url_parent)s,"
              "%(base_ref)s,"
              "%(valid)d,"
              "%(result)s,"
              "%(warning)s,"
              "%(info)s,"
              "%(url)s,"
              "%(line)d,"
              "%(column)d,"
              "%(name)s,"
              "%(checktime)d,"
              "%(dltime)d,"
              "%(dlsize)d,"
              "%(cached)d"
              ")%(separator)s" % \
              {'table': self.dbname,
               'base_url': sqlify(url_data.base_url),
               'recursion_level': url_data.recursion_level,
               'url_parent': sqlify((url_data.parent_url or "")),
               'base_ref': sqlify((url_data.base_ref or "")),
               'valid': intify(url_data.valid),
               'result': sqlify(url_data.result),
               'warning': sqlify(os.linesep.join(url_data.warning)),
               'info': sqlify(os.linesep.join(url_data.info)),
               'url': sqlify(linkcheck.url.url_quote(url_data.url or "")),
               'line': url_data.line,
               'column': url_data.column,
               'name': sqlify(url_data.name),
               'checktime': url_data.checktime,
               'dltime': url_data.dltime,
               'dlsize': url_data.dlsize,
               'cached': intify(url_data.cached),
               'separator': self.separator,
              })
        self.fd.write(os.linesep)
        self.flush()

    def end_output (self, linknumber=-1):
        """print end of checking info as sql comment"""
        if self.fd is None:
            return
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write("-- "+_("Stopped checking at %s (%s)")%\
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write(os.linesep)
        self.flush()
        self.fd = None
