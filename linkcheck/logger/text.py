# -*- coding: iso-8859-1 -*-
"""the default logger"""
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
import os
import time

import linkcheck
import linkcheck.ansicolor
import linkcheck.logger
import linkcheck.strformat
import linkcheck.configuration

from linkcheck.i18n import _


class TextLogger (linkcheck.logger.Logger):
    """A text logger, colorizing the output if possible.

    Every Logger has to implement the following functions:
    start_output (self)
      Called once to initialize the Logger. Why do we not use __init__(self)?
      Because we initialize the start time in start_output and __init__ gets
      not called at the time the checking starts but when the logger object is
      created.
      Another reason is that we might want to create several loggers
      as a default and then switch to another configured output. So we
      must not print anything out at __init__ time.
    
    new_url (self, url_data)
      Called every time an url finished checking. All data we checked is in
      the UrlData object url_data.
    
    end_output (self)
      Called at the end of checking to close filehandles and such.
    
    Passing parameters to the constructor:
    __init__ (self, **args)
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
        """initialize error counter and optional file output"""
        super(TextLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.fd = linkcheck.ansicolor.Colorizer(self.fd)
        self.colorparent = args['colorparent']
        self.colorurl = args['colorurl']
        self.colorname = args['colorname']
        self.colorreal = args['colorreal']
        self.colorbase = args['colorbase']
        self.colorvalid = args['colorvalid']
        self.colorinvalid = args['colorinvalid']
        self.colorinfo = args['colorinfo']
        self.colorwarning = args['colorwarning']
        self.colordltime = args['colordltime']
        self.colordlsize = args['colordlsize']
        self.colorreset = args['colorreset']
        self.errors = 0

    def start_output (self):
        """print generic start checking info"""
        super(TextLogger, self).start_output()
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field('intro'):
            self.fd.write(linkcheck.configuration.AppInfo)
            self.fd.write(os.linesep)
            self.fd.write(linkcheck.configuration.Freeware)
            self.fd.write(os.linesep)
            self.fd.write(_("Get the newest version at %s") %
                          linkcheck.configuration.Url)
            self.fd.write(os.linesep)
            self.fd.write(_("Write comments and bugs to %s") %
                          linkcheck.configuration.Email)
            self.fd.write(os.linesep)
            self.fd.write(os.linesep)
            self.fd.write(_("Start checking at %s") %
                          linkcheck.strformat.strtime(self.starttime))
            self.fd.write(os.linesep)
            self.flush()

    def new_url (self, url_data):
        """print url checking info"""
        if self.fd is None:
            return
        if self.has_field('url'):
            self.write_url(url_data)
        if url_data.name and self.has_field('name'):
            self.write_name(url_data)
        if url_data.parent_url and self.has_field('parenturl'):
            self.write_parent(url_data)
        if url_data.base_ref and self.has_field('base'):
            self.write_base(url_data)
        if url_data.url and self.has_field('realurl'):
            self.write_real(url_data)
        if url_data.dltime >= 0 and self.has_field('dltime'):
            self.write_dltime(url_data)
        if url_data.dlsize >= 0 and self.has_field('dlsize'):
            self.write_dlsize(url_data)
        if url_data.checktime and self.has_field('checktime'):
            self.write_checktime(url_data)
        if url_data.info and self.has_field('info'):
            self.write_info(url_data)
        if url_data.warning and self.has_field('warning'):
            self.write_warning(url_data)
        if self.has_field('result'):
            self.write_result(url_data)
        self.flush()

    def write_url (self, url_data):
        """write url_data.base_url"""
        self.fd.write(os.linesep+self.field('url')+self.spaces('url'))
        txt = repr(url_data.base_url)
        if url_data.cached:
            txt += _(" (cached)")
        self.fd.write(txt, color=self.colorurl)
        self.fd.write(os.linesep)

    def write_name (self, url_data):
        """write url_data.name"""
        self.fd.write(self.field("name")+self.spaces("name"))
        self.fd.write(repr(url_data.name), color=self.colorname)
        self.fd.write(os.linesep)

    def write_parent (self, url_data):
        """write url_data.parent_url"""
        self.fd.write(self.field('parenturl')+self.spaces("parenturl"))
        txt = url_data.parent_url
        txt += _(", line %d")%url_data.line
        txt += _(", col %d")%url_data.column
        self.fd.write(txt, color=self.colorparent)
        self.fd.write(os.linesep)

    def write_base (self, url_data):
        """write url_data.base_ref"""
        self.fd.write(self.field("base")+self.spaces("base"))
        self.fd.write(url_data.base_ref, color=self.colorbase)
        self.fd.write(os.linesep)

    def write_real (self, url_data):
        """write url_data.url"""
        self.fd.write(self.field("realurl")+self.spaces("realurl"))
        self.fd.write(url_data.url, color=self.colorreal)
        self.fd.write(os.linesep)

    def write_dltime (self, url_data):
        """write url_data.dltime"""
        self.fd.write(self.field("dltime")+self.spaces("dltime"))
        self.fd.write(_("%.3f seconds")%url_data.dltime,
                      color=self.colordltime)
        self.fd.write(os.linesep)

    def write_dlsize (self, url_data):
        """write url_data.dlsize"""
        self.fd.write(self.field("dlsize")+self.spaces("dlsize"))
        self.fd.write(linkcheck.strformat.strsize(url_data.dlsize),
                      color=self.colordlsize)
        self.fd.write(os.linesep)

    def write_checktime (self, url_data):
        """write url_data.checktime"""
        self.fd.write(self.field("checktime")+self.spaces("checktime"))
        self.fd.write(_("%.3f seconds") % url_data.checktime,
                      color=self.colordltime)
        self.fd.write(os.linesep)

    def write_info (self, url_data):
        """write url_data.info"""
        text = os.linesep.join(url_data.info)
        text = linkcheck.strformat.wrap(text, 65,
                                   subsequent_indent=" "*self.max_indent)
        self.fd.write(self.field("info")+self.spaces("info"))
        self.fd.write(text, color=self.colorinfo)
        self.fd.write(os.linesep)

    def write_warning (self, url_data):
        """write url_data.warning"""
        text = os.linesep.join(url_data.warning)
        text = linkcheck.strformat.wrap(text, 65,
                                   subsequent_indent=" "*self.max_indent)
        self.fd.write(self.field("warning")+self.spaces("warning"))
        self.fd.write(text, color=self.colorwarning)
        self.fd.write(os.linesep)

    def write_result (self, url_data):
        """write url_data.result"""
        self.fd.write(self.field("result")+self.spaces("result"))
        if url_data.valid:
            color = self.colorvalid
        else:
            self.errors += 1
            color = self.colorinvalid
        self.fd.write(url_data.result, color=color)
        self.fd.write(os.linesep)

    def end_output (self, linknumber=-1):
        """print end of output info, and flush all output buffers"""
        if self.fd is None:
            return
        if self.has_field('outro'):
            self.fd.write(os.linesep+_("Thats it. "))
            if self.errors == 1:
                self.fd.write(_("1 error"))
            else:
                self.fd.write(str(self.errors)+_(" errors"))
            if linknumber >= 0:
                if linknumber == 1:
                    self.fd.write(_(" in 1 link"))
                else:
                    self.fd.write(_(" in %d links") % linknumber)
            self.fd.write(_(" found")+os.linesep)
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write(_("Stopped checking at %s (%s)") % \
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write(os.linesep)
        self.flush()
        self.fd = None
