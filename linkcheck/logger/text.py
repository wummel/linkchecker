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
        esc = linkcheck.ansicolor.esc_ansicolor
        self.colorparent = esc(args['colorparent'])
        self.colorurl = esc(args['colorurl'])
        self.colorname = esc(args['colorname'])
        self.colorreal = esc(args['colorreal'])
        self.colorbase = esc(args['colorbase'])
        self.colorvalid = esc(args['colorvalid'])
        self.colorinvalid = esc(args['colorinvalid'])
        self.colorinfo = esc(args['colorinfo'])
        self.colorwarning = esc(args['colorwarning'])
        self.colordltime = esc(args['colordltime'])
        self.colordlsize = esc(args['colordlsize'])
        self.colorreset = esc(args['colorreset'])
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
            self.fd.write(os.linesep+self.field('url')+self.spaces('url')+
                          self.colorurl+repr(url_data.base_url))
            if url_data.cached:
                self.fd.write(_(" (cached)"))
            self.fd.write(self.colorreset+os.linesep)
        if url_data.name and self.has_field('name'):
            self.fd.write(self.field("name")+self.spaces("name")+
                          self.colorname+repr(url_data.name)+self.colorreset+
                          os.linesep)
        if url_data.parent_url and self.has_field('parenturl'):
            self.fd.write(self.field('parenturl')+self.spaces("parenturl")+
                          self.colorparent+url_data.parent_url+
                          (_(", line %d")%url_data.line)+
                          (_(", col %d")%url_data.column)+
                          self.colorreset+os.linesep)
        if url_data.base_ref and self.has_field('base'):
            self.fd.write(self.field("base")+self.spaces("base")+
                          self.colorbase+repr(url_data.base_ref)+
                          self.colorreset+os.linesep)
        if url_data.url and self.has_field('realurl'):
            self.fd.write(self.field("realurl")+self.spaces("realurl")+
                          self.colorreal+url_data.url+
                          self.colorreset+os.linesep)
        if url_data.dltime >= 0 and self.has_field('dltime'):
            self.fd.write(self.field("dltime")+self.spaces("dltime")+
                          self.colordltime+
                          (_("%.3f seconds")%url_data.dltime)+
                          self.colorreset+os.linesep)
        if url_data.dlsize >= 0 and self.has_field('dlsize'):
            self.fd.write(self.field("dlsize")+self.spaces("dlsize")+
                          self.colordlsize+
                          linkcheck.strformat.strsize(url_data.dlsize)+
                          self.colorreset+os.linesep)
        if url_data.checktime and self.has_field('checktime'):
            self.fd.write(self.field("checktime")+self.spaces("checktime")+
                          self.colordltime+
                          (_("%.3f seconds") % url_data.checktime)+
                          self.colorreset+os.linesep)
        if url_data.info and self.has_field('info'):
            text = os.linesep.join(url_data.info)
            text = linkcheck.strformat.wrap(text, 65,
                                       subsequent_indent=" "*self.max_indent)
            self.fd.write(self.field("info")+self.spaces("info")+text+
                          os.linesep)
        if url_data.warning:
            if self.has_field('warning'):
                text = os.linesep.join(url_data.warning)
                text = linkcheck.strformat.wrap(text, 65,
                                     subsequent_indent=" "*self.max_indent)
                self.fd.write(self.field("warning")+self.spaces("warning")+
                              self.colorwarning+text+
                              self.colorreset+os.linesep)
        if self.has_field('result'):
            self.fd.write(self.field("result")+self.spaces("result"))
            if url_data.valid:
                self.fd.write(self.colorvalid)
            else:
                self.errors += 1
                self.fd.write(self.colorinvalid)
            self.fd.write(url_data.result+self.colorreset+os.linesep)
        self.flush()

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

    def flush (self):
        """If the logger has internal buffers, flush them.
           Ignore flush I/O errors since we are not responsible for proper
           flushing of log output streams.
        """
        if self.fd:
            try:
                self.fd.flush()
            except IOError:
                pass
