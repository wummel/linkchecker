# Copyright (C) 2000-2002  Bastian Kleineidam
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

import sys, time, linkcheck, linkcheck.Config
from Logger import Logger
from linkcheck.log import LogFields, Spaces, strtime, MaxIndent
from linkcheck import StringUtil

class StandardLogger (Logger):
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
        apply(Logger.__init__, (self,), args)
        self.errors = 0
        #self.warnings = 0
        if args.has_key('fileoutput'):
            self.fd = open(args['filename'], "w")
	elif args.has_key('fd'):
            self.fd = args['fd']
        else:
	    self.fd = sys.stdout

    def init (self):
        if self.fd is None: return
        self.starttime = time.time()
        if self.logfield('intro'):
            self.fd.write("%s\n%s\n" % (linkcheck.Config.AppInfo, linkcheck.Config.Freeware))
            self.fd.write(linkcheck._("Get the newest version at %s\n") % linkcheck.Config.Url)
            self.fd.write(linkcheck._("Write comments and bugs to %s\n\n") % linkcheck.Config.Email)
            self.fd.write(linkcheck._("Start checking at %s\n") % linkcheck.log.strtime(self.starttime))
            self.fd.flush()


    def newUrl (self, urlData):
        if self.fd is None: return
        if self.logfield('url'):
            self.fd.write("\n"+LogFields['url']+Spaces['url']+urlData.urlName)
            if urlData.cached:
                self.fd.write(linkcheck._(" (cached)\n"))
            else:
                self.fd.write("\n")
        if urlData.name and self.logfield('name'):
            self.fd.write(LogFields["name"]+Spaces["name"]+urlData.name+"\n")
        if urlData.parentName and self.logfield('parenturl'):
            self.fd.write(LogFields['parenturl']+Spaces["parenturl"]+
	                  urlData.parentName+
                          (linkcheck._(", line %d")%urlData.line)+
                          (linkcheck._(", col %d")%urlData.column)+"\n")
        if urlData.baseRef and self.logfield('base'):
            self.fd.write(LogFields["base"]+Spaces["base"]+urlData.baseRef+"\n")
        if urlData.url and self.logfield('realurl'):
            self.fd.write(LogFields["realurl"]+Spaces["realurl"]+urlData.url+"\n")
        if urlData.dltime>=0 and self.logfield('dltime'):
            self.fd.write(LogFields["dltime"]+Spaces["dltime"]+
	                  linkcheck._("%.3f seconds\n") % urlData.dltime)
        if urlData.dlsize>=0 and self.logfield('dlsize'):
            self.fd.write(LogFields["dlsize"]+Spaces["dlsize"]+
	                  "%s\n"%StringUtil.strsize(urlData.dlsize))
        if urlData.checktime and self.logfield('checktime'):
            self.fd.write(LogFields["checktime"]+Spaces["checktime"]+
	                  linkcheck._("%.3f seconds\n") % urlData.checktime)
        if urlData.infoString and self.logfield('info'):
            self.fd.write(LogFields["info"]+Spaces["info"]+
	                  StringUtil.indent(
                              StringUtil.blocktext(urlData.infoString, 65),
			  MaxIndent)+"\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.logfield('warning'):
                self.fd.write(LogFields["warning"]+Spaces["warning"]+
	                  StringUtil.indent(
                              StringUtil.blocktext(urlData.warningString, 65),
			  MaxIndent)+"\n")

        if self.logfield('result'):
            self.fd.write(LogFields["result"]+Spaces["result"])
            if urlData.valid:
                self.fd.write(urlData.validString+"\n")
            else:
                self.errors += 1
                self.fd.write(urlData.errorString+"\n")
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        if self.logfield('outro'):
            self.fd.write(linkcheck._("\nThats it. "))
            #if self.warnings==1:
            #    self.fd.write(linkcheck._("1 warning, "))
            #else:
            #    self.fd.write(str(self.warnings)+linkcheck._(" warnings, "))
            if self.errors==1:
                self.fd.write(linkcheck._("1 error"))
            else:
                self.fd.write(str(self.errors)+linkcheck._(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(linkcheck._(" in 1 link"))
                else:
                    self.fd.write(linkcheck._(" in %d links") % linknumber)
            self.fd.write(linkcheck._(" found\n"))
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write(linkcheck._("Stopped checking at %s") % linkcheck.log.strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
        self.fd.flush()
        self.fd = None
