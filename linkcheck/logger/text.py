# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2007 Bastian Kleineidam
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

    C{def log_filter_url (self, url_data, do_filter)}
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
        if self.fd is not None:
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

    def start_fileoutput (self):
        super(TextLogger, self).start_fileoutput()
        self.fd = linkcheck.ansicolor.Colorizer(self.fd)

    def start_output (self):
        """
        Write generic start checking info.
        """
        super(TextLogger, self).start_output()
        self.starttime = time.time()
        if self.has_part('intro'):
            self.writeln(linkcheck.configuration.AppInfo)
            self.writeln(linkcheck.configuration.Freeware)
            self.writeln(_("Get the newest version at %(url)s") %
                         {'url': linkcheck.configuration.Url})
            self.writeln(_("Write comments and bugs to %(email)s") %
                         {'email': linkcheck.configuration.Email})
            self.check_date()
            self.writeln()
            self.writeln(_("Start checking at %s") %
                         linkcheck.strformat.strtime(self.starttime))
            self.flush()

    def log_url (self, url_data):
        """
        Write url checking info.
        """
        if self.has_part('url'):
            self.write_url(url_data)
        if url_data.name and self.has_part('name'):
            self.write_name(url_data)
        if url_data.parent_url and self.has_part('parenturl'):
            self.write_parent(url_data)
        if url_data.base_ref and self.has_part('base'):
            self.write_base(url_data)
        if url_data.url and self.has_part('realurl'):
            self.write_real(url_data)
        if url_data.dltime >= 0 and self.has_part('dltime'):
            self.write_dltime(url_data)
        if url_data.dlsize >= 0 and self.has_part('dlsize'):
            self.write_dlsize(url_data)
        if url_data.checktime and self.has_part('checktime'):
            self.write_checktime(url_data)
        if url_data.info and self.has_part('info'):
            self.write_info(url_data)
        if url_data.warnings and self.has_part('warning'):
            self.write_warning(url_data)
        if self.has_part('result'):
            self.write_result(url_data)
        self.flush()

    def write_url (self, url_data):
        """
        Write url_data.base_url.
        """
        self.writeln()
        self.write(self.part('url') + self.spaces('url'))
        txt = u"`%s'" % unicode(url_data.base_url or u"")
        if url_data.cached:
            txt += _(" (cached)")
        self.writeln(txt, color=self.colorurl)

    def write_name (self, url_data):
        """
        Write url_data.name.
        """
        self.write(self.part("name") + self.spaces("name"))
        txt = u"`%s'" % unicode(url_data.name)
        self.writeln(txt, color=self.colorname)

    def write_parent (self, url_data):
        """
        Write url_data.parent_url.
        """
        self.write(self.part('parenturl') + self.spaces("parenturl"))
        txt = url_data.parent_url
        txt += _(", line %d") % url_data.line
        txt += _(", col %d") % url_data.column
        self.writeln(txt, color=self.colorparent)

    def write_base (self, url_data):
        """
        Write url_data.base_ref.
        """
        self.write(self.part("base") + self.spaces("base"))
        self.writeln(url_data.base_ref, color=self.colorbase)

    def write_real (self, url_data):
        """
        Write url_data.url.
        """
        self.write(self.part("realurl") + self.spaces("realurl"))
        self.writeln(unicode(url_data.url), color=self.colorreal)

    def write_dltime (self, url_data):
        """
        Write url_data.dltime.
        """
        self.write(self.part("dltime") + self.spaces("dltime"))
        self.writeln(_("%.3f seconds") % url_data.dltime,
                     color=self.colordltime)

    def write_dlsize (self, url_data):
        """
        Write url_data.dlsize.
        """
        self.write(self.part("dlsize") + self.spaces("dlsize"))
        self.writeln(linkcheck.strformat.strsize(url_data.dlsize),
                     color=self.colordlsize)

    def write_checktime (self, url_data):
        """
        Write url_data.checktime.
        """
        self.write(self.part("checktime") + self.spaces("checktime"))
        self.writeln(_("%.3f seconds") % url_data.checktime,
                     color=self.colordltime)

    def write_info (self, url_data):
        """
        Write url_data.info.
        """
        self.write(self.part("info") + self.spaces("info"))
        text = [x[1] for x in url_data.info]
        self.writeln(self.wrap(text, 65), color=self.colorinfo)

    def write_warning (self, url_data):
        """
        Write url_data.warning.
        """
        self.write(self.part("warning") + self.spaces("warning"))
        text = [x[1] for x in url_data.warnings]
        self.writeln(self.wrap(text, 65), color=self.colorwarning)

    def write_result (self, url_data):
        """
        Write url_data.result.
        """
        self.write(self.part("result") + self.spaces("result"))
        if url_data.valid:
            color = self.colorvalid
            self.write(_("Valid"), color=color)
        else:
            color = self.colorinvalid
            self.write(_("Error"), color=color)
        if url_data.result:
            self.write(u": " + url_data.result, color=color)
        self.writeln()

    def end_output (self):
        """
        Write end of output info, and flush all output buffers.
        """
        if self.has_part('outro'):
            self.writeln()
            self.write(_("That's it.") + " ")
            if self.number >= 0:
                self.write(_n("%d link checked.", "%d links checked.",
                              self.number) % self.number)
                self.write(u" ")
            self.write(_n("%d warning found", "%d warnings found",
                            self.warnings) % self.warnings)
            if self.warnings != self.warnings_printed:
                self.write(_(", %d printed") % self.warnings_printed)
            self.write(u". ")
            self.write(_n("%d error found", "%d errors found",
                            self.errors) % self.errors)
            if self.errors != self.errors_printed:
                self.write(_(", %d printed") % self.errors_printed)
            self.writeln(u".")
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.writeln(_("Stopped checking at %(time)s (%(duration)s)") %
                 {"time": linkcheck.strformat.strtime(self.stoptime),
                  "duration": linkcheck.strformat.strduration_long(duration)})
        self.close_fileoutput()
