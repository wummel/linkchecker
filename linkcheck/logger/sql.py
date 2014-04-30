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
A SQL logger.
"""

import os
from . import _Logger
from .. import url as urlutil


def sqlify (s):
    """
    Escape special SQL chars and strings.
    """
    if not s:
        return "NULL"
    return "'%s'" % s.replace("'", "''").replace(os.linesep, r"\n")


def intify (s):
    """
    Coerce a truth value to 0/1.

    @param s: an object (usually a string)
    @type s: object
    @return: 1 if object truth value is True, else 0
    @rtype: number
    """
    if s:
        return 1
    return 0


class SQLLogger (_Logger):
    """
    SQL output, should work with any SQL database (not tested).
    """

    LoggerName = 'sql'

    LoggerArgs = {
        "filename": "linkchecker-out.sql",
        'separator': ';',
        'dbname': 'linksdb',
    }

    def __init__ (self, **kwargs):
        """Initialize database access data."""
        args = self.get_args(kwargs)
        super(SQLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.dbname = args['dbname']
        self.separator = args['separator']

    def comment (self, s, **args):
        """
        Write SQL comment.
        """
        self.write(u"-- ")
        self.writeln(s=s, **args)

    def start_output (self):
        """
        Write start of checking info as sql comment.
        """
        super(SQLLogger, self).start_output()
        if self.has_part("intro"):
            self.write_intro()
            self.writeln()
            self.flush()

    def log_url (self, url_data):
        """
        Store url check info into the database.
        """
        self.writeln(u"insert into %(table)s(urlname,"
              "parentname,baseref,valid,result,warning,info,url,line,col,"
              "name,checktime,dltime,size,cached,level,modified) values ("
              "%(base_url)s,"
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
              "%(size)d,"
              "%(cached)d,"
              "%(level)d,"
              "%(modified)s"
              ")%(separator)s" %
              {'table': self.dbname,
               'base_url': sqlify(url_data.base_url),
               'url_parent': sqlify((url_data.parent_url)),
               'base_ref': sqlify((url_data.base_ref)),
               'valid': intify(url_data.valid),
               'result': sqlify(url_data.result),
               'warning': sqlify(os.linesep.join(x[1] for x in url_data.warnings)),
               'info': sqlify(os.linesep.join(url_data.info)),
               'url': sqlify(urlutil.url_quote(url_data.url)),
               'line': url_data.line,
               'column': url_data.column,
               'name': sqlify(url_data.name),
               'checktime': url_data.checktime,
               'dltime': url_data.dltime,
               'size': url_data.size,
               'cached': 0,
               'separator': self.separator,
               "level": url_data.level,
               "modified": sqlify(self.format_modified(url_data.modified)),
              })
        self.flush()

    def end_output (self, **kwargs):
        """
        Write end of checking info as sql comment.
        """
        if self.has_part("outro"):
            self.write_outro()
        self.close_fileoutput()
