# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
"""
A HTML logger.
"""

import time
import cgi
import os

import linkcheck.logger
import linkcheck.strformat
import linkcheck.configuration


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
    """
    Logger with HTML output.
    """

    def __init__ (self, **args):
        """
        Initialize default HTML color values.
        """
        super(HtmlLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.colorbackground = args['colorbackground']
        self.colorurl = args['colorurl']
        self.colorborder = args['colorborder']
        self.colorlink = args['colorlink']
        self.colorwarning = args['colorwarning']
        self.colorerror = args['colorerror']
        self.colorok = args['colorok']

    def field (self, name):
        """
        Return non-space-breakable field name.
        """
        return super(HtmlLogger, self).field(name).replace(" ", "&nbsp;")

    def comment (self, s, **args):
        """
        Print HTML comment.
        """
        self.write(u"<!-- ")
        self.write(s, **args)
        self.write(u" -->")

    def start_output (self):
        """
        Print start of checking info.
        """
        super(HtmlLogger, self).start_output()
        if self.fd is None:
            return
        self.starttime = time.time()
        self.write(HTML_HEADER % (linkcheck.configuration.App,
                   self.colorbackground,
                   self.colorlink, self.colorlink, self.colorlink))
        if self.has_field('intro'):
            self.write(u"<center><h2>"+linkcheck.configuration.App+
                       "</h2></center><br><blockquote>"+
                       linkcheck.configuration.Freeware+"<br><br>"+
                       (_("Start checking at %s") % \
                       linkcheck.strformat.strtime(self.starttime))+
                       os.linesep+"<br>")
            self.check_date()
        self.flush()

    def log_url (self, url_data):
        """
        Print url checking info as HTML.
        """
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
        """
        Start html table.
        """
        self.writeln(u"<br clear=\"all\"><br>")
        self.writeln(u"<table align=\"left\" border=\"0\" cellspacing=\"0\""+
                     u" cellpadding=\"1\"")
        self.writeln(u" bgcolor=\""+self.colorborder+
                     u"\" summary=\"Border\">")
        self.writeln(u"<tr>")
        self.writeln(u"<td>")
        self.writeln(u"<table align=\"left\" border=\"0\" cellspacing=\"0\""+
                     u" cellpadding=\"3\"")
        self.writeln(u" summary=\"checked link\" bgcolor=\""+
                     self.colorbackground+u"\">")

    def write_table_end (self):
        """
        End html table.
        """
        self.write(u"</table></td></tr></table><br clear=\"all\">")

    def write_url (self, url_data):
        """
        Write url_data.base_url.
        """
        self.writeln(u"<tr>")
        self.writeln(u"<td bgcolor=\""+self.colorurl+u"\">"+
                     self.field("url")+u"</td>")
        self.write(u"<td bgcolor=\""+self.colorurl+u"\">"+
                   cgi.escape(repr(url_data.base_url)[1:]))
        if url_data.cached:
            self.write(_(" (cached)"))
        self.writeln(u"</td></tr>")

    def write_name (self, url_data):
        """
        Write url_data.name.
        """
        self.writeln(u"<tr><td>"+self.field("name")+u"</td><td>"+
                     cgi.escape(repr(url_data.name)[1:])+u"</td></tr>")

    def write_parent (self, url_data):
        """
        Write url_data.parent_url.
        """
        self.write(u"<tr><td>"+self.field("parenturl")+
                   u'</td><td><a target="top" href="'+
                   url_data.parent_url+u'">'+
                   cgi.escape(url_data.parent_url)+u"</a>")
        self.write(_(", line %d") % url_data.line)
        self.write(_(", col %d") % url_data.column)
        if not url_data.valid:
            # on errors show HTML and CSS validation for parent url
            vhtml = validate_html % {'uri': url_data.parent_url}
            vcss = validate_css % {'uri': url_data.parent_url}
            self.writeln()
            self.writeln(u'(<a href="'+vhtml+u'">HTML</a>)')
            self.write(u'(<a href="'+vcss+u'">CSS</a>)')
        self.writeln(u"</td></tr>")

    def write_base (self, url_data):
        """
        Write url_data.base_ref.
        """
        self.writeln(u"<tr><td>"+self.field("base")+u"</td><td>"+
                     cgi.escape(url_data.base_ref)+u"</td></tr>")

    def write_real (self, url_data):
        """
        Write url_data.url.
        """
        self.writeln("<tr><td>"+self.field("realurl")+u"</td><td>"+
                     u'<a target="top" href="'+url_data.url+
                     u'">'+cgi.escape(url_data.url)+u"</a></td></tr>")

    def write_dltime (self, url_data):
        """
        Write url_data.dltime.
        """
        self.writeln(u"<tr><td>"+self.field("dltime")+u"</td><td>"+
                     (_("%.3f seconds") % url_data.dltime)+
                     u"</td></tr>")

    def write_dlsize (self, url_data):
        """
        Write url_data.dlsize.
        """
        self.writeln(u"<tr><td>"+self.field("dlsize")+u"</td><td>"+
                     linkcheck.strformat.strsize(url_data.dlsize)+
                     u"</td></tr>")

    def write_checktime (self, url_data):
        """
        Write url_data.checktime.
        """
        self.writeln(u"<tr><td>"+self.field("checktime")+u"</td><td>"+
                     (_("%.3f seconds") % url_data.checktime)+u"</td></tr>")

    def write_info (self, url_data):
        """
        Write url_data.info.
        """
        text = os.linesep.join(url_data.info)
        self.writeln(u"<tr><td valign=\"top\">"+self.field("info")+
               u"</td><td>"+cgi.escape(text).replace(os.linesep, "<br>")+
               u"</td></tr>")

    def write_warning (self, url_data):
        """
        Write url_data.warning.
        """
        sep = u"<br>"+os.linesep
        text = sep.join([cgi.escape(x) for x in url_data.warning])
        self.writeln(u"<tr><td bgcolor=\""+self.colorwarning+u"\" "+
                     u"valign=\"top\">"+self.field("warning")+
                     u"</td><td bgcolor=\""+self.colorwarning+u"\">"+
                     text+u"</td></tr>")

    def write_result (self, url_data):
        """
        Write url_data.result.
        """
        if url_data.valid:
            self.write(u"<tr><td bgcolor=\""+self.colorok+u"\">"+
             self.field("result")+u"</td><td bgcolor=\""+self.colorok+u"\">")
            self.write(_("Valid"))
        else:
            self.write(u"<tr><td bgcolor=\""+self.colorerror+u"\">"+
           self.field("result")+u"</td><td bgcolor=\""+self.colorerror+u"\">")
            self.write(_("Error"))
        if url_data.result:
            self.write(u": "+cgi.escape(url_data.result))
        self.writeln(u"</td></tr>")

    def end_output (self):
        """
        Print end of checking info as HTML.
        """
        if self.fd is None:
            return
        if self.has_field("outro"):
            self.writeln()
            self.write(_("That's it.")+" ")
            if self.number >= 0:
                self.write(_n("%d link checked.", "%d links checked.",
                           self.number) % self.number)
                self.write(u" ")
            self.write(_n("%d warning found.", "%d warnings found.",
                            self.warnings) % self.warnings)
            self.write(u" ")
            self.writeln(_n("%d error found.", "%d errors found.",
                         self.errors) % self.errors)
            self.writeln(u"<br>")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.writeln(_("Stopped checking at %s (%s)") % \
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration(duration)))
            self.writeln(u"</blockquote><br><hr noshade size=\"1\"><small>"+
                         linkcheck.configuration.HtmlAppInfo+u"<br>")
            self.writeln(_("Get the newest version at %s") % \
             (u'<a href="'+linkcheck.configuration.Url+u'" target="_top">'+
              linkcheck.configuration.Url+u"</a>.<br>"))
            self.writeln(_("Write comments and bugs to %s") % \
             (u'<a href="mailto:'+linkcheck.configuration.Email+u'">'+
             linkcheck.configuration.Email+u"</a>."))
            self.writeln(u"</small></body></html>")
        self.close_fileoutput()
