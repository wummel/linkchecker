# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2003  Bastian Kleineidam
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
from linkcheck import StringUtil, i18n, AnsiColor


class ColoredLogger (StandardLogger):
    """ANSI colorized output"""

    def __init__ (self, **args):
        super(ColoredLogger, self).__init__(**args)
        self.colorparent = AnsiColor.esc_ansicolor(args['colorparent'])
        self.colorurl = AnsiColor.esc_ansicolor(args['colorurl'])
        self.colorname = AnsiColor.esc_ansicolor(args['colorname'])
        self.colorreal = AnsiColor.esc_ansicolor(args['colorreal'])
        self.colorbase = AnsiColor.esc_ansicolor(args['colorbase'])
        self.colorvalid = AnsiColor.esc_ansicolor(args['colorvalid'])
        self.colorinvalid = AnsiColor.esc_ansicolor(args['colorinvalid'])
        self.colorinfo = AnsiColor.esc_ansicolor(args['colorinfo'])
        self.colorwarning = AnsiColor.esc_ansicolor(args['colorwarning'])
        self.colordltime = AnsiColor.esc_ansicolor(args['colordltime'])
        self.colordlsize = AnsiColor.esc_ansicolor(args['colordlsize'])
        self.colorreset = AnsiColor.esc_ansicolor(args['colorreset'])
        self.currentPage = None
        self.prefix = 0

    def newUrl (self, urlData):
        if self.fd is None: return
        if self.has_field("parenturl"):
            if urlData.parentName:
                if self.currentPage != urlData.parentName:
                    if self.prefix:
                        self.fd.write("o\n")
                    self.fd.write("\n"+self.field("parenturl")+
                              self.spaces("parenturl")+
		              self.colorparent+urlData.parentName+
			      self.colorreset+"\n")
                    self.currentPage = urlData.parentName
                    self.prefix = 1
            else:
                if self.prefix:
                    self.fd.write("o\n")
                self.prefix = 0
                self.currentPage=None
        if self.has_field("url"):
            if self.prefix:
                self.fd.write("|\n+- ")
            else:
                self.fd.write("\n")
            self.fd.write(self.field("url")+self.spaces("url")+self.colorurl+
	              urlData.urlName+self.colorreset)
            if urlData.line:
                self.fd.write(i18n._(", line %d")%urlData.line)
            if urlData.column:
                self.fd.write(i18n._(", col %d")%urlData.column)
            if urlData.cached:
                self.fd.write(i18n._(" (cached)\n"))
            else:
                self.fd.write("\n")

        if urlData.name and self.has_field("name"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("name")+self.spaces("name")+
                          self.colorname+urlData.name+self.colorreset+"\n")
        if urlData.baseRef and self.has_field("base"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("base")+self.spaces("base")+
                          self.colorbase+urlData.baseRef+self.colorreset+"\n")
            
        if urlData.url and self.has_field("realurl"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("realurl")+self.spaces("realurl")+
                          self.colorreal+urlData.url+self.colorreset+"\n")
        if urlData.dltime>=0 and self.has_field("dltime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("dltime")+self.spaces("dltime")+
                          self.colordltime+
                          (i18n._("%.3f seconds") % urlData.dltime)+
                          self.colorreset+"\n")
        if urlData.dlsize>=0 and self.has_field("dlsize"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("dlsize")+self.spaces("dlsize")+
                          self.colordlsize+StringUtil.strsize(urlData.dlsize)+
                          self.colorreset+"\n")
        if urlData.checktime and self.has_field("checktime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("checktime")+self.spaces("checktime")+
                self.colordltime+
	        (i18n._("%.3f seconds") % urlData.checktime)+self.colorreset+"\n")
            
        if urlData.infoString and self.has_field("info"):
            if self.prefix:
                self.fd.write("|  "+self.field("info")+self.spaces("info")+
                      StringUtil.indentWith(StringUtil.blocktext(
                      urlData.infoString, 65), "|      "+self.spaces("info")))
            else:
                self.fd.write(self.field("info")+self.spaces("info")+
                      StringUtil.indentWith(StringUtil.blocktext(
                        urlData.infoString, 65), "    "+self.spaces("info")))
            self.fd.write(self.colorreset+"\n")
            
        if urlData.warningString:
            #self.warnings += 1
            if self.has_field("warning"):
                if self.prefix:
                    self.fd.write("|  ")
                self.fd.write(self.field("warning")+self.spaces("warning")+
		          self.colorwarning+
	                  urlData.warningString+self.colorreset+"\n")

        if self.has_field("result"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("result")+self.spaces("result"))
            if urlData.valid:
                self.fd.write(self.colorvalid+urlData.validString+
	                      self.colorreset+"\n")
            else:
                self.errors += 1
                self.fd.write(self.colorinvalid+urlData.errorString+
	                      self.colorreset+"\n")
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        if self.has_field("outro"):
            if self.prefix:
                self.fd.write("o\n")
        super(ColoredLogger, self).endOfOutput(linknumber=linknumber)

