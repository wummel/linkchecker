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

from StandardLogger import StandardLogger
from linkcheck import Config
from linkcheck.log import strtime
import time, linkcheck

HTML_HEADER = """<!DOCTYPE html PUBLIC "-//W3C//DTD html 4.0//EN">
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
<body bgcolor=%s link=%s vlink=%s alink=%s>
"""

class HtmlLogger (StandardLogger):
    """Logger with HTML output"""

    def __init__ (self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def init (self):
        if self.fd is None: return
        self.starttime = time.time()
        self.fd.write(HTML_HEADER%(Config.App, self.colorbackground,
                      self.colorlink, self.colorlink, self.colorlink))
        if self.logfield('intro'):
            self.fd.write("<center><h2>"+Config.App+"</h2></center>"+
              "<br><blockquote>"+Config.Freeware+"<br><br>"+
              (linkcheck._("Start checking at %s\n") % strtime(self.starttime))+
	      "<br><br>")
        self.fd.flush()

    def newUrl (self, urlData):
        if self.fd is None: return
        self.fd.write('<table align=left border=0 cellspacing=0'
              ' cellpadding=1 bgcolor='+self.colorborder+' summary=Border'
              '><tr><td><table align=left border=0 cellspacing=0'
              ' cellpadding=3 summary="checked link" bgcolor='+
	      self.colorbackground+">")
        if self.logfield("url"):
	    self.fd.write("<tr><td bgcolor="+self.colorurl+">"+linkcheck._("URL")+
              "</td><td bgcolor="+self.colorurl+">"+urlData.urlName)
            if urlData.cached:
                self.fd.write(linkcheck._(" (cached)\n"))
            self.fd.write("</td></tr>\n")
        if urlData.name and self.logfield("name"):
            self.fd.write("<tr><td>"+linkcheck._("Name")+"</td><td>"+
                          urlData.name+"</td></tr>\n")
        if urlData.parentName and self.logfield("parenturl"):
            self.fd.write("<tr><td>"+linkcheck._("Parent URL")+"</td><td>"+
			  '<a href="'+urlData.parentName+'">'+
                          urlData.parentName+"</a> line "+str(urlData.line)+
                          "</td></tr>\n")
        if urlData.baseRef and self.logfield("base"):
            self.fd.write("<tr><td>"+linkcheck._("Base")+"</td><td>"+
	                  urlData.baseRef+"</td></tr>\n")
        if urlData.url and self.logfield("realurl"):
            self.fd.write("<tr><td>"+linkcheck._("Real URL")+"</td><td>"+
	                  '<a href="'+urlData.url+
			  '">'+urlData.url+"</a></td></tr>\n")
        if urlData.downloadtime and self.logfield("dltime"):
            self.fd.write("<tr><td>"+linkcheck._("D/L Time")+"</td><td>"+
	                  (linkcheck._("%.3f seconds") % urlData.downloadtime)+
			  "</td></tr>\n")
        if urlData.checktime and self.logfield("checktime"):
            self.fd.write("<tr><td>"+linkcheck._("Check Time")+
	                  "</td><td>"+
			  (linkcheck._("%.3f seconds") % urlData.checktime)+
			  "</td></tr>\n")
        if urlData.infoString and self.logfield("info"):
            self.fd.write("<tr><td>"+linkcheck._("Info")+"</td><td>"+
	                  linkcheck.StringUtil.htmlify(urlData.infoString)+
			  "</td></tr>\n")
        if urlData.warningString:
            #self.warnings += 1
            if self.logfield("warning"):
                self.fd.write("<tr>"+self.tablewarning+linkcheck._("Warning")+
	                  "</td>"+self.tablewarning+
                          urlData.warningString.replace("\n", "<br>")+
			  "</td></tr>\n")
        if self.logfield("result"):
            if urlData.valid:
                self.fd.write("<tr>"+self.tableok+linkcheck._("Result")+"</td>"+
                  self.tableok+urlData.validString+"</td></tr>\n")
            else:
                self.errors += 1
                self.fd.write("<tr>"+self.tableerror+linkcheck._("Result")+
	                  "</td>"+self.tableerror+
			  urlData.errorString+"</td></tr>\n")
        self.fd.write("</table></td></tr></table><br clear=all><br>")
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        if self.logfield("outro"):
            self.fd.write("\n"+linkcheck._("Thats it. "))
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
            self.fd.write(linkcheck._(" found")+"\n<br>")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write(linkcheck._("Stopped checking at %s") % strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write("	(%.3f %s)\n" % (duration, name))
            self.fd.write("</blockquote><br><hr noshade size=1><small>"+
             Config.HtmlAppInfo+"<br>")
            self.fd.write(linkcheck._("Get the newest version at %s\n") %\
             ('<a href="'+Config.Url+'" target=_top>'+Config.Url+
	      "</a>.<br>"))
            self.fd.write(linkcheck._("Write comments and bugs to %s\n\n") %\
	     ('<a href="mailto:'+Config.Email+'">'+Config.Email+"</a>."))
            self.fd.write("</small></body></html>")
        self.fd.flush()
        self.fd = None

