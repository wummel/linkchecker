# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
The default text logger.
"""
import time
from . import _Logger
from .. import ansicolor, strformat, configuration, i18n


class TextLogger (_Logger):
    """
    A text logger, colorizing the output if possible.

    Informal text output format spec:
    Output consists of a set of URL logs separated by one or more
    blank lines.
    A URL log consists of two or more lines. Each line consists of
    keyword and data, separated by whitespace.
    Unknown keywords will be ignored.
    """

    LoggerName = 'text'

    LoggerArgs = {
        "filename": "linkchecker-out.txt",
        'colorparent':  "default",
        'colorurl':     "default",
        'colorname':    "default",
        'colorreal':    "cyan",
        'colorbase':    "purple",
        'colorvalid':   "bold;green",
        'colorinvalid': "bold;red",
        'colorinfo':    "default",
        'colorwarning': "bold;yellow",
        'colordltime':  "default",
        'colordlsize':  "default",
        'colorreset':   "default",
    }

    def __init__ (self, **kwargs):
        """Initialize error counter and optional file output."""
        args = self.get_args(kwargs)
        super(TextLogger, self).__init__(**args)
        self.output_encoding = args.get("encoding", i18n.default_encoding)
        self.init_fileoutput(args)
        self.colorparent = args.get('colorparent', 'default')
        self.colorurl = args.get('colorurl', 'default')
        self.colorname = args.get('colorname', 'default')
        self.colorreal = args.get('colorreal', 'default')
        self.colorbase = args.get('colorbase', 'default')
        self.colorvalid = args.get('colorvalid', 'default')
        self.colorinvalid = args.get('colorinvalid', 'default')
        self.colorinfo = args.get('colorinfo', 'default')
        self.colorwarning = args.get('colorwarning', 'default')
        self.colordltime = args.get('colordltime', 'default')
        self.colordlsize = args.get('colordlsize', 'default')
        self.colorreset = args.get('colorreset', 'default')

    def init_fileoutput (self, args):
        """Colorize file output if possible."""
        super(TextLogger, self).init_fileoutput(args)
        if self.fd is not None:
            self.fd = ansicolor.Colorizer(self.fd)

    def start_fileoutput (self):
        """Needed to make file descriptor color aware."""
        init_color = self.fd is None
        super(TextLogger, self).start_fileoutput()
        if init_color:
            self.fd = ansicolor.Colorizer(self.fd)

    def start_output (self):
        """Write generic start checking info."""
        super(TextLogger, self).start_output()
        if self.has_part('intro'):
            self.write_intro()
        self.flush()

    def write_intro (self):
        """Log introduction text."""
        self.writeln(configuration.AppInfo)
        self.writeln(configuration.Freeware)
        self.writeln(_("Get the newest version at %(url)s") %
                     {'url': configuration.Url})
        self.writeln(_("Write comments and bugs to %(url)s") %
                     {'url': configuration.SupportUrl})
        self.writeln(_("Support this project at %(url)s") %
                     {'url': configuration.DonateUrl})
        self.check_date()
        self.writeln()
        self.writeln(_("Start checking at %s") %
                     strformat.strtime(self.starttime))

    def log_url (self, url_data):
        """Write url checking info."""
        self.writeln()
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
        if url_data.checktime and self.has_part('checktime'):
            self.write_checktime(url_data)
        if url_data.dltime >= 0 and self.has_part('dltime'):
            self.write_dltime(url_data)
        if url_data.size >= 0 and self.has_part('dlsize'):
            self.write_size(url_data)
        if url_data.info and self.has_part('info'):
            self.write_info(url_data)
        if url_data.modified and self.has_part('modified'):
            self.write_modified(url_data)
        if url_data.warnings and self.has_part('warning'):
            self.write_warning(url_data)
        if self.has_part('result'):
            self.write_result(url_data)
        self.flush()

    def write_id (self):
        """Write unique ID of url_data."""
        self.writeln()
        self.write(self.part('id') + self.spaces('id'))
        self.writeln(u"%d" % self.stats.number, color=self.colorinfo)

    def write_url (self, url_data):
        """Write url_data.base_url."""
        self.write(self.part('url') + self.spaces('url'))
        txt = strformat.strline(url_data.base_url)
        self.writeln(txt, color=self.colorurl)

    def write_name (self, url_data):
        """Write url_data.name."""
        self.write(self.part("name") + self.spaces("name"))
        self.writeln(strformat.strline(url_data.name), color=self.colorname)

    def write_parent (self, url_data):
        """Write url_data.parent_url."""
        self.write(self.part('parenturl') + self.spaces("parenturl"))
        txt = url_data.parent_url
        if url_data.line > 0:
            txt += _(", line %d") % url_data.line
        if url_data.column > 0:
            txt += _(", col %d") % url_data.column
        if url_data.page > 0:
            txt += _(", page %d") % url_data.page
        self.writeln(txt, color=self.colorparent)

    def write_base (self, url_data):
        """Write url_data.base_ref."""
        self.write(self.part("base") + self.spaces("base"))
        self.writeln(url_data.base_ref, color=self.colorbase)

    def write_real (self, url_data):
        """Write url_data.url."""
        self.write(self.part("realurl") + self.spaces("realurl"))
        self.writeln(unicode(url_data.url), color=self.colorreal)

    def write_dltime (self, url_data):
        """Write url_data.dltime."""
        self.write(self.part("dltime") + self.spaces("dltime"))
        self.writeln(_("%.3f seconds") % url_data.dltime,
                     color=self.colordltime)

    def write_size (self, url_data):
        """Write url_data.size."""
        self.write(self.part("dlsize") + self.spaces("dlsize"))
        self.writeln(strformat.strsize(url_data.size),
                     color=self.colordlsize)

    def write_checktime (self, url_data):
        """Write url_data.checktime."""
        self.write(self.part("checktime") + self.spaces("checktime"))
        self.writeln(_("%.3f seconds") % url_data.checktime,
                     color=self.colordltime)

    def write_info (self, url_data):
        """Write url_data.info."""
        self.write(self.part("info") + self.spaces("info"))
        self.writeln(self.wrap(url_data.info, 65), color=self.colorinfo)

    def write_modified(self, url_data):
        """Write url_data.modified."""
        self.write(self.part("modified") + self.spaces("modified"))
        self.writeln(self.format_modified(url_data.modified))

    def write_warning (self, url_data):
        """Write url_data.warning."""
        self.write(self.part("warning") + self.spaces("warning"))
        warning_msgs = [u"[%s] %s" % x for x in url_data.warnings]
        self.writeln(self.wrap(warning_msgs, 65), color=self.colorwarning)

    def write_result (self, url_data):
        """Write url_data.result."""
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

    def write_outro (self, interrupt=False):
        """Write end of checking message."""
        self.writeln()
        if interrupt:
            self.writeln(_("The check has been interrupted; results are not complete."))
        self.write(_("That's it.") + " ")
        self.write(_n("%d link", "%d links",
                      self.stats.number) % self.stats.number)
        self.write(u" ")
        if self.stats.num_urls is not None:
            self.write(_n("in %d URL", "in %d URLs",
                          self.stats.num_urls) % self.stats.num_urls)
        self.write(u" checked. ")
        warning_text = _n("%d warning found", "%d warnings found",
             self.stats.warnings_printed) % self.stats.warnings_printed
        if self.stats.warnings_printed:
            warning_color = self.colorwarning
        else:
            warning_color = self.colorinfo
        self.write(warning_text, color=warning_color)
        if self.stats.warnings != self.stats.warnings_printed:
            self.write(_(" (%d ignored or duplicates not printed)") %
                (self.stats.warnings - self.stats.warnings_printed))
        self.write(u". ")
        error_text = _n("%d error found", "%d errors found",
             self.stats.errors_printed) % self.stats.errors_printed
        if self.stats.errors_printed:
            error_color = self.colorinvalid
        else:
            error_color = self.colorvalid
        self.write(error_text, color=error_color)
        if self.stats.errors != self.stats.errors_printed:
            self.write(_(" (%d duplicates not printed)") %
                (self.stats.errors - self.stats.errors_printed))
        self.writeln(u".")
        num = self.stats.internal_errors
        if num:
            self.writeln(_n("There was %(num)d internal error.",
                "There were %(num)d internal errors.", num) % {"num": num})
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        self.writeln(_("Stopped checking at %(time)s (%(duration)s)") %
             {"time": strformat.strtime(self.stoptime),
              "duration": strformat.strduration_long(duration)})

    def write_stats (self):
        """Write check statistic info."""
        self.writeln()
        self.writeln(_("Statistics:"))
        if self.stats.downloaded_bytes is not None:
            self.writeln(_("Downloaded: %s.") % strformat.strsize(self.stats.downloaded_bytes))
        if self.stats.number > 0:
            self.writeln(_(
              "Content types: %(image)d image, %(text)d text, %(video)d video, "
              "%(audio)d audio, %(application)d application, %(mail)d mail"
              " and %(other)d other.") % self.stats.link_types)
            self.writeln(_("URL lengths: min=%(min)d, max=%(max)d, avg=%(avg)d.") %
                         dict(min=self.stats.min_url_length,
                         max=self.stats.max_url_length,
                         avg=self.stats.avg_url_length))
        else:
            self.writeln(_("No statistics available since no URLs were checked."))

    def end_output (self, **kwargs):
        """Write end of output info, and flush all output buffers."""
        self.stats.downloaded_bytes = kwargs.get("downloaded_bytes")
        self.stats.num_urls = kwargs.get("num_urls")
        if self.has_part('stats'):
            self.write_stats()
        if self.has_part('outro'):
            self.write_outro(interrupt=kwargs.get("interrupt"))
        self.close_fileoutput()
