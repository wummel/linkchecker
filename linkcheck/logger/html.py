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
import linkcheck.strformat
import linkcheck.configuration

from linkcheck.i18n import _


# ss=1 enables show source
validate_html = "http://validator.w3.org/check?ss=1&amp;uri=%(uri)s"
# options are the default
validate_css = "http://jigsaw.w3.org/css-validator/validator?" \
               "uri=%(uri)s&amp;warning=1&amp;profile=css2&amp;usermedium=all"

HTML_HEADER = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
 "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>%s</title>
<style type="text/css">
<!--
 h2 { font-family: Verdana,sans-serif; font-size: 22pt;
 font-style: bold; font-weight: bold }
 body { font-family: Arial,sans-serif; font-size: 11pt }
 td { font-family: Arial,sans-serif; font-size: 11pt }
 code { font-family: Courier }
 a:hover { color: #34a4ef }
 //-->
</style>
</head>
<body bgcolor="%s" link="%s" vlink="%s" alink="%s">
"""

class HtmlLogger (linkcheck.logger.Logger):
    """Logger with HTML output"""

    def __init__ (self, **args):
        """initialize default HTML color values"""
        super(HtmlLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.tablewarning = args['tablewarning']
        self.tableerror = args['tableerror']
        self.tableok = args['tableok']

    def start_output (self):
        """print start of checking info"""
        super(HtmlLogger, self).start_output()
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
                          (_("Start checking at %s") % \
                          linkcheck.strformat.strtime(self.starttime))+
                          os.linesep+"<br>")
        self.flush()

    def new_url (self, url_data):
        """print url checking info as HTML"""
        if self.fd is None:
            return
        self.write_table_start()
        if self.has_field("url"):
            self.write_url(url_data)
        if url_data.name and self.has_field("name"):
            self.write_name(url_data)
        if url_data.parent_url and self.has_field("parenturl"):
            self.write_parent(url_data)
        if url_data.base_ref and self.has_field("base"):
            self.write_base(url_data)
        if url_data.url and self.has_field("realurl"):
            self.write_real(url_data)
        if url_data.dltime >= 0 and self.has_field("dltime"):
            self.write_dltime(url_data)
        if url_data.dlsize >= 0 and self.has_field("dlsize"):
            self.write_dlsize(url_data)
        if url_data.checktime and self.has_field("checktime"):
            self.write_checktime(url_data)
        if url_data.info and self.has_field("info"):
            self.write_info(url_data)
        if url_data.warning and self.has_field("warning"):
            self.write_warning(url_data)
        if self.has_field("result"):
            self.write_result(url_data)
        self.write_table_end()
        self.flush()

    def write_table_start (self):
        """start html table"""
        self.fd.write("<br clear=\"all\"><br>"+os.linesep+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\""+
             " cellpadding=\"1\""+os.linesep+
             " bgcolor=\""+self.colorborder+
             "\" summary=\"Border\">"+os.linesep+
             "<tr>"+os.linesep+
             "<td>"+os.linesep+
             "<table align=\"left\" border=\"0\" cellspacing=\"0\""+
             " cellpadding=\"3\""+os.linesep+
             " summary=\"checked link\" bgcolor=\""+self.colorbackground+
             "\">"+os.linesep)

    def write_table_end (self):
        """end html table"""
        self.fd.write("</table></td></tr></table><br clear=\"all\">")

    def write_url (self, url_data):
        """write url_data.base_url"""
        self.fd.write("<tr>"+os.linesep+
             "<td bgcolor=\""+self.colorurl+"\">"+self.field("url")+"</td>"+
             os.linesep+
             "<td bgcolor=\""+self.colorurl+"\">"+url_data.base_url)
        if url_data.cached:
            self.fd.write(_(" (cached)"))
        self.fd.write("</td></tr>"+os.linesep)

    def write_name (self, url_data):
        """write url_data.name"""
        self.fd.write("<tr><td>"+self.field("name")+"</td><td>"+
                      cgi.escape(url_data.name)+"</td></tr>"+os.linesep)

    def write_parent (self, url_data):
        """write url_data.parent_url"""
        self.fd.write("<tr><td>"+self.field("parenturl")+
               '</td><td><a target="top" href="'+
               url_data.parent_url+'">'+
               cgi.escape(url_data.parent_url)+"</a>")
        self.fd.write(_(", line %d")%url_data.line)
        self.fd.write(_(", col %d")%url_data.column)
        if not url_data.valid:
            # on errors show HTML and CSS validation for parent url
            vhtml = validate_html % {'url': url_data.parent_url}
            vcss = validate_css % {'url': url_data.parent_url}
            self.fd.write(os.linesep)
            self.fd.write('(<a href="'+vhtml+'">HTML</a>)')
            self.fd.write(os.linesep)
            self.fd.write('(<a href="'+vcss+'">CSS</a>)')
        self.fd.write("</td></tr>"+os.linesep)

    def write_base (self, url_data):
        """write url_data.base_ref"""
        self.fd.write("<tr><td>"+self.field("base")+"</td><td>"+
                      cgi.escape(url_data.base_ref)+"</td></tr>"+os.linesep)

    def write_real (self, url_data):
        """write url_data.url"""
        self.fd.write("<tr><td>"+self.field("realurl")+"</td><td>"+
                      '<a target="top" href="'+url_data.url+
                      '">'+cgi.escape(url_data.url)+"</a></td></tr>"+
                      os.linesep)

    def write_dltime (self, url_data):
        """write url_data.dltime"""
        self.fd.write("<tr><td>"+self.field("dltime")+"</td><td>"+
                      (_("%.3f seconds") % url_data.dltime)+
                      "</td></tr>"+os.linesep)

    def write_dlsize (self, url_data):
        """write url_data.dlsize"""
        self.fd.write("<tr><td>"+self.field("dlsize")+"</td><td>"+
                      linkcheck.strformat.strsize(url_data.dlsize)+
                      "</td></tr>"+os.linesep)

    def write_checktime (self, url_data):
        """write url_data.checktime"""
        self.fd.write("<tr><td>"+self.field("checktime")+
                      "</td><td>"+
                      (_("%.3f seconds") % url_data.checktime)+
                      "</td></tr>"+os.linesep)

    def write_info (self, url_data):
        """write url_data.info"""
        text = os.linesep.join(url_data.info)
        self.fd.write("<tr><td>"+self.field("info")+"</td><td>"+
            cgi.escape(text).replace(os.linesep, "<br>")+
            "</td></tr>"+os.linesep)

    def write_warning (self, url_data):
        """write url_data.warning"""
        text = os.linesep.join(url_data.warning)
        self.fd.write("<tr>"+
                      self.tablewarning+self.field("warning")+
                      "</td>"+self.tablewarning+
                      cgi.escape(text).replace(os.linesep, "<br>")+
                      "</td></tr>"+os.linesep)

    def write_result (self, url_data):
        """write url_data.result"""
        if url_data.valid:
            self.fd.write("<tr>"+self.tableok+
              self.field("result")+"</td>"+self.tableok+
              cgi.escape(url_data.result)+"</td></tr>"+os.linesep)
        else:
            self.errors += 1
            self.fd.write("<tr>"+self.tableerror+self.field("result")+
                      "</td>"+self.tableerror+
                      cgi.escape(url_data.result)+"</td></tr>"+os.linesep)

    def end_output (self, linknumber=-1):
        """print end of checking info as HTML"""
        if self.fd is None:
            return
        if self.has_field("outro"):
            self.fd.write(os.linesep+_("Thats it. "))
            if self.errors == 1:
                self.fd.write(_("1 error"))
            else:
                self.fd.write(_("%d errors") % self.errors)
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(_(" in 1 link"))
                else:
                    self.fd.write(_(" in %d links") % linknumber)
            self.fd.write(_(" found")+"<br>"+os.linesep)
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write(_("Stopped checking at %s (%s)")%\
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write(os.linesep)
            self.fd.write("</blockquote><br><hr noshade size=\"1\"><small>"+
                          linkcheck.configuration.HtmlAppInfo+"<br>")
            self.fd.write(_("Get the newest version at %s") %\
             ('<a href="'+linkcheck.configuration.Url+'" target="_top">'+
             linkcheck.configuration.Url+
              "</a>.<br>")+os.linesep)
            self.fd.write(_("Write comments and bugs to %s") %\
             ('<a href="mailto:'+linkcheck.configuration.Email+'">'+
             linkcheck.configuration.Email+"</a>.")+os.linesep)
            self.fd.write("</small></body></html>"+os.linesep)
        self.flush()
        self.fd = None
