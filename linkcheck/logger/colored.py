# -*- coding: iso-8859-1 -*-
"""a colored logger"""
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

import os

import linkcheck
import linkcheck.ansicolor
import linkcheck.logger.standard

from linkcheck.i18n import _


class ColoredLogger (linkcheck.logger.standard.StandardLogger):
    """ANSI colorized output"""

    def __init__ (self, **args):
        """initialize standard colors"""
        super(ColoredLogger, self).__init__(**args)
        self.colorparent = linkcheck.ansicolor.esc_ansicolor(
                                                        args['colorparent'])
        self.colorurl = linkcheck.ansicolor.esc_ansicolor(args['colorurl'])
        self.colorname = linkcheck.ansicolor.esc_ansicolor(args['colorname'])
        self.colorreal = linkcheck.ansicolor.esc_ansicolor(args['colorreal'])
        self.colorbase = linkcheck.ansicolor.esc_ansicolor(args['colorbase'])
        self.colorvalid = linkcheck.ansicolor.esc_ansicolor(
                                                          args['colorvalid'])
        self.colorinvalid = linkcheck.ansicolor.esc_ansicolor(
                                                        args['colorinvalid'])
        self.colorinfo = linkcheck.ansicolor.esc_ansicolor(args['colorinfo'])
        self.colorwarning = linkcheck.ansicolor.esc_ansicolor(
                                                        args['colorwarning'])
        self.colordltime = linkcheck.ansicolor.esc_ansicolor(
                                                         args['colordltime'])
        self.colordlsize = linkcheck.ansicolor.esc_ansicolor(
                                                         args['colordlsize'])
        self.colorreset = linkcheck.ansicolor.esc_ansicolor(
                                                         args['colorreset'])
        self.currentPage = None
        self.prefix = 0

    def new_url (self, url_data):
        """print new url data in color"""
        if self.fd is None:
            return
        if self.has_field("parenturl"):
            if url_data.parent_url:
                if self.currentPage != url_data.parent_url:
                    if self.prefix:
                        self.fd.write("o"+os.linesep)
                    self.fd.write(os.linesep+self.field("parenturl")+
                              self.spaces("parenturl")+
                              self.colorparent+
                              (url_data.parent_url or "")+
                              self.colorreset+os.linesep)
                    self.currentPage = url_data.parent_url
                    self.prefix = 1
            else:
                if self.prefix:
                    self.fd.write("o"+os.linesep)
                self.prefix = 0
                self.currentPage = None
        if self.has_field("url"):
            if self.prefix:
                self.fd.write("|"+os.linesep+"+- ")
            else:
                self.fd.write(os.linesep)
            self.fd.write(self.field("url")+self.spaces("url")+self.colorurl+
                      url_data.base_url+self.colorreset)
            if url_data.line:
                self.fd.write(_(", line %d")%url_data.line)
            if url_data.column:
                self.fd.write(_(", col %d")%url_data.column)
            if url_data.cached:
                self.fd.write(_(" (cached)")+os.linesep)
            else:
                self.fd.write(os.linesep)

        if url_data.name and self.has_field("name"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("name")+self.spaces("name")+
                          self.colorname+url_data.name+self.colorreset+
                          os.linesep)
        if url_data.base_ref and self.has_field("base"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("base")+self.spaces("base")+
                          self.colorbase+url_data.base_ref+self.colorreset+
                          os.linesep)

        if url_data.url and self.has_field("realurl"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("realurl")+self.spaces("realurl")+
                          self.colorreal+url_data.url+
                          self.colorreset+os.linesep)
        if url_data.dltime >= 0 and self.has_field("dltime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("dltime")+self.spaces("dltime")+
                          self.colordltime+
                          (_("%.3f seconds") % url_data.dltime)+
                          self.colorreset+os.linesep)
        if url_data.dlsize >= 0 and self.has_field("dlsize"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("dlsize")+self.spaces("dlsize")+
                          self.colordlsize+
                          linkcheck.strformat.strsize(url_data.dlsize)+
                          self.colorreset+os.linesep)
        if url_data.checktime and self.has_field("checktime"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("checktime")+self.spaces("checktime")+
                self.colordltime+(_("%.3f seconds") % url_data.checktime)+
                self.colorreset+os.linesep)

        if url_data.info and self.has_field("info"):
            if self.prefix:
                text = os.linesep.join(url_data.info)
                text = linkcheck.strformat.wrap(text, 65,
                             subsequent_indent="|      "+self.spaces("info"))
                self.fd.write("|  "+self.field("info")+
                              self.spaces("info")+text)
            else:
                text = os.linesep.join(url_data.info)
                text = linkcheck.strformat.wrap(text, 65,
                               subsequent_indent="    "+self.spaces("info"))
                self.fd.write(self.field("info")+self.spaces("info")+text)
            self.fd.write(self.colorreset+os.linesep)

        if url_data.warning and self.has_field("warning"):
            if self.prefix:
                self.fd.write("|  ")
            text = os.linesep.join(url_data.warning)
            self.fd.write(self.field("warning")+self.spaces("warning")+
                          self.colorwarning+text+self.colorreset+os.linesep)

        if self.has_field("result"):
            if self.prefix:
                self.fd.write("|  ")
            self.fd.write(self.field("result")+self.spaces("result"))
            if url_data.valid:
                self.fd.write(self.colorvalid+url_data.result+
                              self.colorreset+os.linesep)
            else:
                self.errors += 1
                self.fd.write(self.colorinvalid+url_data.result+
                              self.colorreset+os.linesep)
        self.flush()

    def end_output (self, linknumber=-1):
        """print end of checking message and flush output buffers"""
        if self.fd is None:
            return
        if self.has_field("outro"):
            if self.prefix:
                self.fd.write("o"+os.linesep)
        super(ColoredLogger, self).end_output(linknumber=linknumber)
