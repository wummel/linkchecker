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

import sys
import time
import bk.i18n
import bk.url
import linkcheck.logger.Logger


class StandardLogger (linkcheck.logger.Logger.Logger):
    """Standard text logger.

Every Logger has to implement the following functions:
init(self)
  Called once to initialize the Logger. Why do we not use __init__(self)?
  Because we initialize the start time in init and __init__ gets not
  called at the time the checking starts but when the logger object is
  created.
  Another reason is that we dont want might create several loggers
  as a default and then switch to another configured output. So we
  must not print anything out at __init__ time.

newUrl(self,urlData)
  Called every time an url finished checking. All data we checked is in
  the UrlData object urlData.

endOfOutput(self)
  Called at the end of checking to close filehandles and such.

Passing parameters to the constructor:
__init__(self, **args)
  The args dictionary is filled in Config.py. There you can specify
  default parameters. Adjust these parameters in the configuration
  files in the appropriate logger section.

    Informal text output format spec:
    Output consists of a set of URL logs separated by one or more
    blank lines.
    A URL log consists of two or more lines. Each line consists of
    keyword and data, separated by whitespace.
    Unknown keywords will be ignored.
    """

    def __init__ (self, **args):
        super(StandardLogger, self).__init__(**args)
        self.errors = 0
        #self.warnings = 0
        if args.has_key('fileoutput'):
            self.fd = file(args['filename'], "w")
	elif args.has_key('fd'):
            self.fd = args['fd']
        else:
	    self.fd = sys.stdout

    def init (self):
        super(StandardLogger, self).init()
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field('intro'):
            self.fd.write("%s\n%s\n" % (linkcheck.Config.AppInfo, linkcheck.Config.Freeware))
            self.fd.write(bk.i18n._("Get the newest version at %s\n") % linkcheck.Config.Url)
            self.fd.write(bk.i18n._("Write comments and bugs to %s\n\n") % linkcheck.Config.Email)
            self.fd.write(bk.i18n._("Start checking at %s\n") % bk.strtime.strtime(self.starttime))
            self.flush()

    def newUrl (self, urlData):
        if self.fd is None:
            return
        if self.has_field('url'):
            self.fd.write("\n"+self.field('url')+self.spaces('url')+
                          urlData.urlName)
            if urlData.cached:
                self.fd.write(bk.i18n._(" (cached)\n"))
            else:
                self.fd.write("\n")
        if urlData.name and self.has_field('name'):
            self.fd.write(self.field("name")+self.spaces("name")+
                          urlData.name+"\n")
        if urlData.parentName and self.has_field('parenturl'):
            self.fd.write(self.field('parenturl')+self.spaces("parenturl")+
	                  bk.url.url_quote(urlData.parentName or "")+
                          (bk.i18n._(", line %d")%urlData.line)+
                          (bk.i18n._(", col %d")%urlData.column)+"\n")
        if urlData.baseRef and self.has_field('base'):
            self.fd.write(self.field("base")+self.spaces("base")+
                          urlData.baseRef+"\n")
        if urlData.url and self.has_field('realurl'):
            self.fd.write(self.field("realurl")+self.spaces("realurl")+
                          bk.url.url_quote(urlData.url)+"\n")
        if urlData.dltime>=0 and self.has_field('dltime'):
            self.fd.write(self.field("dltime")+self.spaces("dltime")+
	                  bk.i18n._("%.3f seconds\n") % urlData.dltime)
        if urlData.dlsize>=0 and self.has_field('dlsize'):
            self.fd.write(self.field("dlsize")+self.spaces("dlsize")+
	                  "%s\n"%linkcheck.StringUtil.strsize(urlData.dlsize))
        if urlData.checktime and self.has_field('checktime'):
            self.fd.write(self.field("checktime")+self.spaces("checktime")+
	                  bk.i18n._("%.3f seconds\n") % urlData.checktime)
        if urlData.infoString and self.has_field('info'):
            self.fd.write(self.field("info")+self.spaces("info")+
	                  linkcheck.StringUtil.indent(
                              linkcheck.StringUtil.blocktext(urlData.infoString, 65),
			  self.max_indent)+"\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.has_field('warning'):
                self.fd.write(self.field("warning")+self.spaces("warning")+
	                  linkcheck.StringUtil.indent(
                              linkcheck.StringUtil.blocktext(urlData.warningString, 65),
			  self.max_indent)+"\n")

        if self.has_field('result'):
            self.fd.write(self.field("result")+self.spaces("result"))
            if urlData.valid:
                self.fd.write(urlData.validString+"\n")
            else:
                self.errors += 1
                self.fd.write(urlData.errorString+"\n")
        self.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None:
            return
        if self.has_field('outro'):
            self.fd.write(bk.i18n._("\nThats it. "))
            #if self.warnings==1:
            #    self.fd.write(bk.i18n._("1 warning, "))
            #else:
            #    self.fd.write(str(self.warnings)+bk.i18n._(" warnings, "))
            if self.errors==1:
                self.fd.write(bk.i18n._("1 error"))
            else:
                self.fd.write(str(self.errors)+bk.i18n._(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(bk.i18n._(" in 1 link"))
                else:
                    self.fd.write(bk.i18n._(" in %d links") % linknumber)
            self.fd.write(bk.i18n._(" found\n"))
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write(bk.i18n._("Stopped checking at %s (%s)\n") % \
                          (bk.strtime.strtime(self.stoptime),
                           bk.strtime.strduration(duration)))
        self.flush()
        self.fd = None

    def flush (self):
        """ignore flush errors since we are not responsible for proper
           flushing of log output streams"""
        if self.fd:
            try:
                self.fd.flush()
            except IOError:
                pass
