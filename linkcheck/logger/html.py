# -*- coding: iso-8859-1 -*-
"""a html logger"""
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
import cgi
import os

import linkcheck.logger
import linkcheck.logger.standard
import linkcheck.strformat
import linkcheck.configuration

from linkcheck.i18n import _


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

class HtmlLogger (linkcheck.logger.standard.StandardLogger):
    """Logger with HTML output"""

    def __init__ (self, **args):
        """initialize default HTML color values"""
        super(HtmlLogger, self).__init__(**args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def start_output (self):
        """print start of checking info"""
        linkcheck.logger.Logger.start_output(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        self.fd.write(HTML_HEADER % (linkcheck.configuration.App,
                      self.colorbackground,
                      self.colorlink, self.colorlink, self.colorlink))
        if self.has_field('intro'):
            self.fd.write("<center><h2>"+linkcheck.configuration.App+
                          "</h2></center><br><blockquote>"+
                          linkcheck.configuration.Freeware+"<br><br>"+
                          (_("Start checking at %s\n") % \
                          linkcheck.strformat.strtime(self.starttime))+
                          "<br>")
        self.flush()

    def new_url (self, url_data):
        """print url checking info as HTML"""
        if self.fd is None:
            return
        self.fd.write("<br clear=\"all\"><br>\n"+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\""+
             " cellpadding=\"1\"\n"+
             " bgcolor=\""+self.colorborder+"\" summary=\"Border\">\n"+
             "<tr>\n"+
             "<td>\n"+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\""+
             " cellpadding=\"3\"\n"+
             " summary=\"checked link\" bgcolor=\""+self.colorbackground+
             "\">\n")
        if self.has_field("url"):
            self.fd.write("<tr>\n"+
             "<td bgcolor=\""+self.colorurl+"\">"+self.field("url")+"</td>\n"+
             "<td bgcolor=\""+self.colorurl+"\">"+url_data.base_url)
            if url_data.cached:
                self.fd.write(_(" (cached)"))
            self.fd.write("</td>\n</tr>\n")
        if url_data.name and self.has_field("name"):
            self.fd.write("<tr>\n<td>"+self.field("name")+"</td>\n<td>"+
                          url_data.name+"</td>\n</tr>\n")
        if url_data.parent_url and self.has_field("parenturl"):
            self.fd.write("<tr>\n<td>"+self.field("parenturl")+
               '</td>\n<td><a target="top" href="'+
               (url_data.parent_url or "")+'">'+
               (url_data.parent_url or "")+"</a>")
            if url_data.line:
                self.fd.write(_(", line %d")%url_data.line)
            if url_data.column:
                self.fd.write(_(", col %d")%url_data.column)
            self.fd.write("</td>\n</tr>\n")
        if url_data.base_ref and self.has_field("base"):
            self.fd.write("<tr>\n<td>"+self.field("base")+"</td>\n<td>"+
                          url_data.base_ref+"</td>\n</tr>\n")
        if url_data.url and self.has_field("realurl"):
            self.fd.write("<tr>\n<td>"+self.field("realurl")+"</td>\n<td>"+
                          '<a target="top" href="'+url_data.url+
                          '">'+url_data.url+"</a></td>\n</tr>\n")
        if url_data.dltime >= 0 and self.has_field("dltime"):
            self.fd.write("<tr>\n<td>"+self.field("dltime")+"</td>\n<td>"+
                          (_("%.3f seconds") % url_data.dltime)+
                          "</td>\n</tr>\n")
        if url_data.dlsize >= 0 and self.has_field("dlsize"):
            self.fd.write("<tr>\n<td>"+self.field("dlsize")+"</td>\n<td>"+
                          linkcheck.strformat.strsize(url_data.dlsize)+
                          "</td>\n</tr>\n")
        if url_data.checktime and self.has_field("checktime"):
            self.fd.write("<tr>\n<td>"+self.field("checktime")+
                          "</td>\n<td>"+
                          (_("%.3f seconds") % url_data.checktime)+
                          "</td>\n</tr>\n")
        if url_data.info and self.has_field("info"):
            text = os.linesep.join(url_data.info)
            self.fd.write("<tr>\n<td>"+self.field("info")+"</td>\n<td>"+
                cgi.escape(text).replace(os.linesep, "<br>")+
                "</td>\n</tr>\n")
        if url_data.warning and self.has_field("warning"):
            text = os.linesep.join(url_data.warning)
            self.fd.write("<tr>\n"+
              self.tablewarning+self.field("warning")+
              "</td>\n"+self.tablewarning+
              cgi.escape(text).replace(os.linesep, "<br>")+
              "</td>\n</tr>\n")
        if self.has_field("result"):
            if url_data.valid:
                self.fd.write("<tr>\n"+self.tableok+
                  self.field("result")+"</td>\n"+
                  self.tableok+url_data.result+"</td>\n</tr>\n")
            else:
                self.errors += 1
                self.fd.write("<tr>\n"+self.tableerror+self.field("result")+
                          "</td>\n"+self.tableerror+
                          url_data.result+"</td>\n</tr>\n")
        self.fd.write("</table></td></tr></table><br clear=\"all\">")
        self.flush()

    def end_output (self, linknumber=-1):
        """print end of checking info as HTML"""
        if self.fd is None:
            return
        if self.has_field("outro"):
            self.fd.write("\n"+_("Thats it. "))
            #if self.warnings == 1:
            #    self.fd.write(_("1 warning, "))
            #else:
            #    self.fd.write(str(self.warnings)+_(" warnings, "))
            if self.errors == 1:
                self.fd.write(_("1 error"))
            else:
                self.fd.write(str(self.errors)+_(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(_(" in 1 link"))
                else:
                    self.fd.write(_(" in %d links") % linknumber)
            self.fd.write(_(" found")+"\n<br>")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write(_("Stopped checking at %s (%s)\n")%\
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write("</blockquote><br><hr noshade size=\"1\"><small>"+
                          linkcheck.configuration.HtmlAppInfo+"<br>")
            self.fd.write(_("Get the newest version at %s\n") %\
             ('<a href="'+linkcheck.configuration.Url+'" target="_top">'+
             linkcheck.configuration.Url+
              "</a>.<br>"))
            self.fd.write(_("Write comments and bugs to %s\n\n") %\
             ('<a href="mailto:'+linkcheck.configuration.Email+'">'+
             linkcheck.configuration.Email+"</a>."))
            self.fd.write("</small></body></html>")
        self.flush()
        self.fd = None
