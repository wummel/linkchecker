# -*- coding: iso-8859-1 -*-
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

from StandardLogger import StandardLogger
from Logger import Logger
import time
from linkcheck.log import strtime, strduration
from linkcheck import StringUtil, i18n, Config

class SQLLogger (StandardLogger):
    """ SQL output for PostgreSQL, not tested"""
    def __init__ (self, **args):
        super(SQLLogger, self).__init__(**args)
        self.dbname = args['dbname']
        self.separator = args['separator']


    def init (self):
        Logger.init(self)
        if self.fd is None: return
        self.starttime = time.time()
        if self.has_field("intro"):
            self.fd.write("-- "+(i18n._("created by %s at %s\n") % (Config.AppName,
                       strtime(self.starttime))))
            self.fd.write("-- "+(i18n._("Get the newest version at %s\n") % Config.Url))
            self.fd.write("-- "+(i18n._("Write comments and bugs to %s\n\n") % \
	                Config.Email))
            self.fd.flush()


    def newUrl (self, urlData):
        if self.fd is None: return
        self.fd.write("insert into %s(urlname,recursionlevel,parentname,"
              "baseref,errorstring,validstring,warningstring,infostring,"
	      "valid,url,line,col,name,checktime,dltime,dlsize,cached)"
              " values "
              "(%s,%d,%s,%s,%s,%s,%s,%s,%d,%s,%d,%d,%s,%d,%d,%d,%d)%s\n" % \
	      (self.dbname,
	       StringUtil.sqlify(urlData.urlName),
               urlData.recursionLevel,
	       StringUtil.sqlify(urlData.parentName),
               StringUtil.sqlify(urlData.baseRef),
               StringUtil.sqlify(urlData.errorString),
               StringUtil.sqlify(urlData.validString),
               StringUtil.sqlify(urlData.warningString),
               StringUtil.sqlify(urlData.infoString),
               urlData.valid,
               StringUtil.sqlify(urlData.url),
               urlData.line,
               urlData.column,
               StringUtil.sqlify(urlData.name),
               urlData.checktime,
               urlData.dltime,
               urlData.dlsize,
               urlData.cached,
	       self.separator))
        self.fd.flush()


    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write("-- "+i18n._("Stopped checking at %s (%s)\n")%\
	                  (strtime(self.stoptime), strduration(duration)))
        self.fd.flush()
        self.fd = None
