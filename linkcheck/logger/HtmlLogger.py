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

import time
import linkcheck.logger.StandardLogger
import bk.i18n
import bk.url


HTML_HEADER = """<!DOCTYPE html PUBLIC "-//W3C//DTD html 4.01//EN">
<html><head><title>%s</title>
<style type="text/css">\n<!--
 h2 { font-family: Verdana,sans-serif; font-size: 22pt;
 font-style: bold; font-weight: bold }
 body { font-family: Arial,sans-serif; font-size: 11pt }
 td { font-family: Arial,sans-serif; font-size: 11pt }
 code { font-family: Courier }
 a:hover { color: #34a4ef }
 //-->
</style></head>
<body bgcolor="%s" link="%s" vlink="%s" alink="%s">
"""

class HtmlLogger (linkcheck.logger.StandardLogger.StandardLogger):
    """Logger with HTML output"""

    def __init__ (self, **args):
        super(HtmlLogger, self).__init__(**args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def init (self):
        linkcheck.logger.Logger.Logger.init(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        self.fd.write(HTML_HEADER%(linkcheck.Config.App, self.colorbackground,
                      self.colorlink, self.colorlink, self.colorlink))
        if self.has_field('intro'):
            self.fd.write("<center><h2>"+linkcheck.Config.App+"</h2></center>"+
              "<br><blockquote>"+linkcheck.Config.Freeware+"<br><br>"+
              (bk.i18n._("Start checking at %s\n") % \
               bk.strtime.strtime(self.starttime))+
	      "<br>")
        self.flush()

    def newUrl (self, urlData):
        if self.fd is None:
            return
        self.fd.write("<br clear=\"all\"><br>\n"+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\" cellpadding=\"1\"\n"+
             " bgcolor=\""+self.colorborder+"\" summary=\"Border\">\n"+
             "<tr>\n"+
             "<td>\n"+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\" cellpadding=\"3\"\n"+
             " summary=\"checked link\" bgcolor=\""+self.colorbackground+"\">\n")
        if self.has_field("url"):
	    self.fd.write("<tr>\n"+
             "<td bgcolor=\""+self.colorurl+"\">"+self.field("url")+"</td>\n"+
             "<td bgcolor=\""+self.colorurl+"\">"+urlData.urlName)
            if urlData.cached:
                self.fd.write(bk.i18n._(" (cached)"))
            self.fd.write("</td>\n</tr>\n")
        if urlData.name and self.has_field("name"):
            self.fd.write("<tr>\n<td>"+self.field("name")+"</td>\n<td>"+
                          urlData.name+"</td>\n</tr>\n")
        if urlData.parentName and self.has_field("parenturl"):
            self.fd.write("<tr>\n<td>"+self.field("parenturl")+
               '</td>\n<td><a target="top" href="'+
               bk.url.url_quote(urlData.parentName or "")+'">'+
               bk.url.url_quote(urlData.parentName or "")+"</a>")
            if urlData.line:
                self.fd.write(bk.i18n._(", line %d")%urlData.line)
            if urlData.column:
                self.fd.write(bk.i18n._(", col %d")%urlData.column)
            self.fd.write("</td>\n</tr>\n")
        if urlData.baseRef and self.has_field("base"):
            self.fd.write("<tr>\n<td>"+self.field("base")+"</td>\n<td>"+
	                  urlData.baseRef+"</td>\n</tr>\n")
        if urlData.url and self.has_field("realurl"):
            self.fd.write("<tr>\n<td>"+self.field("realurl")+"</td>\n<td>"+
	                  '<a target="top" href="'+bk.url.url_quote(urlData.url)+
			  '">'+bk.url.url_quote(urlData.url)+"</a></td>\n</tr>\n")
        if urlData.dltime>=0 and self.has_field("dltime"):
            self.fd.write("<tr>\n<td>"+self.field("dltime")+"</td>\n<td>"+
	                  (bk.i18n._("%.3f seconds") % urlData.dltime)+
			  "</td>\n</tr>\n")
        if urlData.dlsize>=0 and self.has_field("dlsize"):
            self.fd.write("<tr>\n<td>"+self.field("dlsize")+"</td>\n<td>"+
	                  linkcheck.StringUtil.strsize(urlData.dlsize)+
			  "</td>\n</tr>\n")
        if urlData.checktime and self.has_field("checktime"):
            self.fd.write("<tr>\n<td>"+self.field("checktime")+
	                  "</td>\n<td>"+
			  (bk.i18n._("%.3f seconds") % urlData.checktime)+
			  "</td>\n</tr>\n")
        if urlData.infoString and self.has_field("info"):
            self.fd.write("<tr>\n<td>"+self.field("info")+"</td>\n<td>"+
	                  linkcheck.StringUtil.htmlify(urlData.infoString)+
			  "</td>\n</tr>\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.has_field("warning"):
                self.fd.write("<tr>\n"+
                    self.tablewarning+self.field("warning")+
	            "</td>\n"+self.tablewarning+
                    urlData.warningString.replace("\n", "<br>")+
                    "</td>\n</tr>\n")
        if self.has_field("result"):
            if urlData.valid:
                self.fd.write("<tr>\n"+self.tableok+
                  self.field("result")+"</td>\n"+
                  self.tableok+urlData.validString+"</td>\n</tr>\n")
            else:
                self.errors += 1
                self.fd.write("<tr>\n"+self.tableerror+self.field("result")+
	                  "</td>\n"+self.tableerror+
			  urlData.errorString+"</td>\n</tr>\n")
        self.fd.write("</table></td></tr></table><br clear=\"all\">")
        self.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None:
            return
        if self.has_field("outro"):
            self.fd.write("\n"+bk.i18n._("Thats it. "))
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
            self.fd.write(bk.i18n._(" found")+"\n<br>")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write(bk.i18n._("Stopped checking at %s (%s)\n")%\
                          (bk.strtime.strtime(self.stoptime),
                           bk.strtime.strduration(duration)))
            self.fd.write("</blockquote><br><hr noshade size=\"1\"><small>"+
                          linkcheck.Config.HtmlAppInfo+"<br>")
            self.fd.write(bk.i18n._("Get the newest version at %s\n") %\
             ('<a href="'+linkcheck.Config.Url+'" target="_top">'+linkcheck.Config.Url+
	      "</a>.<br>"))
            self.fd.write(bk.i18n._("Write comments and bugs to %s\n\n") %\
	     ('<a href="mailto:'+linkcheck.Config.Email+'">'+linkcheck.Config.Email+"</a>."))
            self.fd.write("</small></body></html>")
        self.flush()
        self.fd = None
