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
The default text logger.
"""

import time

import linkcheck
import linkcheck.ansicolor
import linkcheck.logger
import linkcheck.strformat
import linkcheck.configuration


class TextLogger (linkcheck.logger.Logger):
    """
    A text logger, colorizing the output if possible.

    Every Logger has to implement the following functions:

    C{def start_output (self)}
    Called once to initialize the Logger. Why do we not use __init__(self)?
    Because we initialize the start time in start_output and __init__ gets
    not called at the time the checking starts but when the logger object is
    created.
    Another reason is that we might want to create several loggers
    as a default and then switch to another configured output. So we
    must not print anything out at __init__ time.

    C{def new_url (self, url_data)}
    Called every time an url finished checking. All data we checked is in
    the UrlData object url_data.

    C{def end_output (self)}
    Called at the end of checking to close filehandles and such.

    Passing parameters to the constructor:

    C{def __init__ (self, **args)}
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
        """
        Initialize error counter and optional file output.
        """
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

    def start_output (self):
        """
        Print generic start checking info.
        """
        super(TextLogger, self).start_output()
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field('intro'):
            self.writeln(linkcheck.configuration.AppInfo)
            self.writeln(linkcheck.configuration.Freeware)
            self.writeln(_("Get the newest version at %s") %
                         linkcheck.configuration.Url)
            self.writeln(_("Write comments and bugs to %s") %
                         linkcheck.configuration.Email)
            self.check_date()
            self.writeln()
            self.writeln(_("Start checking at %s") %
                         linkcheck.strformat.strtime(self.starttime))
            self.flush()

    def new_url (self, url_data):
        """
        Print url checking info.
        """
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
        """
        Write url_data.base_url.
        """
        self.writeln()
        self.write(self.field('url') + self.spaces('url'))
        txt = unicode(repr(url_data.base_url)[1:])
        if url_data.cached:
            txt += _(" (cached)")
        self.writeln(txt, color=self.colorurl)

    def write_name (self, url_data):
        """
        Write url_data.name.
        """
        self.write(self.field("name") + self.spaces("name"))
        self.writeln(unicode(repr(url_data.name)[1:]), color=self.colorname)

    def write_parent (self, url_data):
        """
        Write url_data.parent_url.
        """
        self.write(self.field('parenturl') + self.spaces("parenturl"))
        txt = url_data.parent_url
        txt += _(", line %d") % url_data.line
        txt += _(", col %d") % url_data.column
        self.writeln(txt, color=self.colorparent)

    def write_base (self, url_data):
        """
        Write url_data.base_ref.
        """
        self.write(self.field("base") + self.spaces("base"))
        self.writeln(url_data.base_ref, color=self.colorbase)

    def write_real (self, url_data):
        """
        Write url_data.url.
        """
        self.write(self.field("realurl") + self.spaces("realurl"))
        self.writeln(unicode(url_data.url), color=self.colorreal)

    def write_dltime (self, url_data):
        """
        Write url_data.dltime.
        """
        self.write(self.field("dltime") + self.spaces("dltime"))
        self.writeln(_("%.3f seconds") % url_data.dltime,
                     color=self.colordltime)

    def write_dlsize (self, url_data):
        """
        Write url_data.dlsize.
        """
        self.write(self.field("dlsize") + self.spaces("dlsize"))
        self.writeln(linkcheck.strformat.strsize(url_data.dlsize),
                     color=self.colordlsize)

    def write_checktime (self, url_data):
        """
        Write url_data.checktime.
        """
        self.write(self.field("checktime") + self.spaces("checktime"))
        self.writeln(_("%.3f seconds") % url_data.checktime,
                     color=self.colordltime)

    def write_info (self, url_data):
        """
        Write url_data.info.
        """
        self.write(self.field("info") + self.spaces("info"))
        self.writeln(self.wrap(url_data.info, 65), color=self.colorinfo)

    def write_warning (self, url_data):
        """
        Write url_data.warning.
        """
        self.write(self.field("warning") + self.spaces("warning"))
        self.writeln(self.wrap(url_data.warning, 65), color=self.colorwarning)

    def write_result (self, url_data):
        """
        Write url_data.result.
        """
        self.write(self.field("result") + self.spaces("result"))
        if url_data.valid:
            color = self.colorvalid
            self.write(_("Valid"), color=color)
        else:
            self.errors += 1
            color = self.colorinvalid
            self.write(_("Error"), color=color)
        if url_data.result:
            self.write(u": "+url_data.result, color=color)
        self.writeln()

    def end_output (self, linknumber=-1):
        """
        Print end of output info, and flush all output buffers.
        """
        if self.fd is None:
            return
        if self.has_field('outro'):
            self.writeln()
            self.write(_("That's it.")+" ")
            if linknumber >= 0:
                self.write(_n("%d link checked.", "%d links checked.",
                              linknumber) % linknumber)
                self.write(u" ")

            self.writeln(_n("%d error found.", "%d errors found.",
                            self.errors) % self.errors)
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.writeln(_("Stopped checking at %s (%s)") % \
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration(duration)))
        self.flush()
        if self.close_fd:
            self.fd.close()
        self.fd = None
