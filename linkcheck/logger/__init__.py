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
Output logging support for different formats.
"""

import sys
import os
import datetime
import time
import codecs
import abc
from .. import log, LOG_CHECK, strformat, dummy, configuration, i18n

_ = lambda x: x
Fields = dict(
    realurl=_("Real URL"),
    cachekey=_("Cache key"),
    result=_("Result"),
    base=_("Base"),
    name=_("Name"),
    parenturl=_("Parent URL"),
    extern=_("Extern"),
    info=_("Info"),
    warning=_("Warning"),
    dltime=_("D/L time"),
    dlsize=_("Size"),
    checktime=_("Check time"),
    url=_("URL"),
    level=_("Level"),
    modified=_("Modified"),
)
del _

ContentTypes = dict(
    image=0,
    text=0,
    video=0,
    audio=0,
    application=0,
    mail=0,
    other=0,
)


class LogStatistics (object):
    """Gather log statistics:
    - number of errors, warnings and valid links
    - type of contents (image, video, audio, text, ...)
    - URL lengths
    """

    def __init__ (self):
        """Initialize log statistics."""
        self.reset()

    def reset (self):
        """Reset all log statistics to default values."""
        # number of logged URLs
        self.number = 0
        # number of encountered URL errors
        self.errors = 0
        # number of URL errors that were printed
        self.errors_printed = 0
        # number of URL warnings
        self.warnings = 0
        # number of URL warnings that were printed
        self.warnings_printed = 0
        # number of internal errors
        self.internal_errors = 0
        # link types
        self.link_types = ContentTypes.copy()
        # URL length statistics
        self.max_url_length = 0
        self.min_url_length = 0
        self.avg_url_length = 0.0
        self.avg_number = 0
        # overall downloaded bytes
        self.downloaded_bytes = None

    def log_url (self, url_data, do_print):
        """Log URL statistics."""
        self.number += 1
        if not url_data.valid:
            self.errors += 1
            if do_print:
                self.errors_printed += 1
        num_warnings = len(url_data.warnings)
        self.warnings += num_warnings
        if do_print:
            self.warnings_printed += num_warnings
        if url_data.content_type:
            key = url_data.content_type.split('/', 1)[0].lower()
            if key not in self.link_types:
                key = "other"
        elif url_data.url.startswith(u"mailto:"):
            key = "mail"
        else:
            key = "other"
        self.link_types[key] += 1
        if url_data.url:
            l = len(url_data.url)
            self.max_url_length = max(l, self.max_url_length)
            if self.min_url_length == 0:
                self.min_url_length = l
            else:
                self.min_url_length = min(l, self.min_url_length)
            # track average number separately since empty URLs do not count
            self.avg_number += 1
            # calculate running average
            self.avg_url_length += (l - self.avg_url_length) / self.avg_number

    def log_internal_error (self):
        """Increase internal error count."""
        self.internal_errors += 1


class _Logger (object):
    """
    Base class for logging of checked urls. It defines the public API
    (see below) and offers basic functionality for all loggers.

    Each logger offers the following functions:

    * start_output()
        Initialize and start log output. Most loggers print a comment
        with copyright information.
    * end_output(**kwargs)
        Finish log output, possibly flushing buffers. Most loggers also
        print some statistics.
        Custom keyword arguments can be given for different loggers.
    * log_filter_url(url_data, do_print)
        Log a checked URL. The url_data object is a transport form of
        the UrlData class. The do_print flag indicates if this URL
        should be logged or just used to update internal statistics.

    Each subclassed logger must implement the following functions:

    * start_output()
        Also call the base class implementation of this.
    * end_output(**kwargs)
        See above.
    * log_url(url_data)
        Log a checked URL. Called by log_filter_url if do_print is True.
    """
    __metaclass__ = abc.ABCMeta

    # A lowercase name for this logger, usable for option values
    LoggerName = None

    # Default log configuration
    LoggerArgs = {}

    def __init__ (self, **args):
        """
        Initialize a logger, looking for part restrictions in kwargs.
        """
        if 'parts' in args and "all" not in args['parts']:
            # only log given parts
            self.logparts = args['parts']
        else:
            # log all parts
            self.logparts = None
        # number of spaces before log parts for alignment
        self.logspaces = {}
        # maximum indent of spaces for alignment
        self.max_indent = 0
        # log statistics
        self.stats = LogStatistics()
        # encoding of output
        encoding = args.get("encoding", i18n.default_encoding)
        try:
            encoding = codecs.lookup(encoding).name
        except LookupError:
            encoding = i18n.default_encoding
        self.output_encoding = encoding
        # how to handle codec errors
        self.codec_errors = "replace"
        # Flag to see if logger is active. Can be deactivated on errors.
        self.is_active = True

    def get_args(self, kwargs):
        """Construct log configuration from default and user args."""
        args = dict(self.LoggerArgs)
        args.update(kwargs)
        return args

    def get_charset_encoding (self):
        """Translate the output encoding to a charset encoding name."""
        if self.output_encoding == "utf-8-sig":
            return "utf-8"
        return self.output_encoding

    def encode (self, s):
        """Encode string with output encoding."""
        assert isinstance(s, unicode)
        return s.encode(self.output_encoding, self.codec_errors)

    def init_fileoutput (self, args):
        """
        Initialize self.fd file descriptor from args. For file output
        (used when the fileoutput arg is given), the self.fd
        initialization is deferred until the first self.write() call.
        This avoids creation of an empty file when no output is written.
        """
        self.filename = None
        self.close_fd = False
        self.fd = None
        if args.get('fileoutput'):
            self.filename = os.path.expanduser(args['filename'])
        elif 'fd' in args:
            self.fd = args['fd']
        else:
            self.fd = self.create_fd()

    def start_fileoutput (self):
        """Start output to configured file."""
        path = os.path.dirname(self.filename)
        try:
            if path and not os.path.isdir(path):
                os.makedirs(path)
            self.fd = self.create_fd()
            self.close_fd = True
        except IOError:
            msg = sys.exc_info()[1]
            log.warn(LOG_CHECK,
                "Could not open file %r for writing: %s\n"
                "Disabling log output of %s", self.filename, msg, self)
            self.fd = dummy.Dummy()
            self.is_active = False
        self.filename = None

    def create_fd (self):
        """Create open file descriptor."""
        if self.filename is None:
            return i18n.get_encoded_writer(encoding=self.output_encoding,
                                           errors=self.codec_errors)
        return codecs.open(self.filename, "wb", self.output_encoding,
                           self.codec_errors)

    def close_fileoutput (self):
        """
        Flush and close the file output denoted by self.fd.
        """
        if self.fd is not None:
            try:
                self.flush()
            except IOError:
                # ignore flush errors
                pass
            if self.close_fd:
                try:
                    self.fd.close()
                except IOError:
                    # ignore close errors
                    pass
            self.fd = None

    def check_date (self):
        """
        Check for special dates.
        """
        now = datetime.date.today()
        if now.day == 7 and now.month == 1:
            msg = _("Happy birthday for LinkChecker, I'm %d years old today!")
            self.comment(msg % (now.year - 2000))

    def comment (self, s, **args):
        """
        Write a comment and a newline. This method just prints
        the given string.
        """
        self.writeln(s=s, **args)

    def wrap (self, lines, width):
        """
        Return wrapped version of given lines.
        """
        sep = os.linesep+os.linesep
        text = sep.join(lines)
        kwargs = dict(subsequent_indent=" "*self.max_indent,
                      initial_indent=" "*self.max_indent,
                      break_long_words=False,
                      break_on_hyphens=False)
        return strformat.wrap(text, width, **kwargs).lstrip()

    def write (self, s, **args):
        """Write string to output descriptor. Strips control characters
        from string before writing.
        """
        if self.filename is not None:
            self.start_fileoutput()
        if self.fd is None:
            # Happens when aborting threads times out
            log.warn(LOG_CHECK, "writing to unitialized or closed file")
        else:
            try:
                self.fd.write(s, **args)
            except IOError:
                msg = sys.exc_info()[1]
                log.warn(LOG_CHECK,
                    "Could not write to output file: %s\n"
                    "Disabling log output of %s", msg, self)
                self.close_fileoutput()
                self.fd = dummy.Dummy()
                self.is_active = False

    def writeln (self, s=u"", **args):
        """
        Write string to output descriptor plus a newline.
        """
        self.write(u"%s%s" % (s, unicode(os.linesep)), **args)

    def has_part (self, name):
        """
        See if given part name will be logged.
        """
        if self.logparts is None:
            # log all parts
            return True
        return name in self.logparts

    def part (self, name):
        """
        Return translated part name.
        """
        return _(Fields.get(name, u""))

    def spaces (self, name):
        """
        Return indent of spaces for given part name.
        """
        return self.logspaces[name]

    def start_output (self):
        """
        Start log output.
        """
        # map with spaces between part name and value
        if self.logparts is None:
            parts = Fields.keys()
        else:
            parts = self.logparts
        values = (self.part(x) for x in parts)
        # maximum indent for localized log part names
        self.max_indent = max(len(x) for x in values)+1
        for key in parts:
            numspaces = (self.max_indent - len(self.part(key)))
            self.logspaces[key] = u" " * numspaces
        self.stats.reset()
        self.starttime = time.time()

    def log_filter_url (self, url_data, do_print):
        """
        Log a new url with this logger if do_print is True. Else
        only update accounting data.
        """
        self.stats.log_url(url_data, do_print)
        if do_print:
            self.log_url(url_data)

    def write_intro (self):
        """Write intro comments."""
        self.comment(_("created by %(app)s at %(time)s") %
                    {"app": configuration.AppName,
                     "time": strformat.strtime(self.starttime)})
        self.comment(_("Get the newest version at %(url)s") %
                     {'url': configuration.Url})
        self.comment(_("Write comments and bugs to %(url)s") %
                     {'url': configuration.SupportUrl})
        self.comment(_("Support this project at %(url)s") %
                     {'url': configuration.DonateUrl})
        self.check_date()

    def write_outro (self):
        """Write outro comments."""
        self.stoptime = time.time()
        duration = self.stoptime - self.starttime
        self.comment(_("Stopped checking at %(time)s (%(duration)s)") %
             {"time": strformat.strtime(self.stoptime),
              "duration": strformat.strduration_long(duration)})

    @abc.abstractmethod
    def log_url (self, url_data):
        """
        Log a new url with this logger.
        """
        pass

    @abc.abstractmethod
    def end_output (self, **kwargs):
        """
        End of output, used for cleanup (eg output buffer flushing).
        """
        pass

    def __str__ (self):
        """
        Return class name.
        """
        return self.__class__.__name__

    def __repr__ (self):
        """
        Return class name.
        """
        return repr(self.__class__.__name__)

    def flush (self):
        """
        If the logger has internal buffers, flush them.
        Ignore flush I/O errors since we are not responsible for proper
        flushing of log output streams.
        """
        if hasattr(self, "fd"):
            try:
                self.fd.flush()
            except (IOError, AttributeError):
                pass

    def log_internal_error (self):
        """Indicate that an internal error occurred in the program."""
        log.warn(LOG_CHECK, "internal error occurred")
        self.stats.log_internal_error()

    def format_modified(self, modified, sep=" "):
        """Format modification date in UTC if it's not None.
        @param modified: modification date in UTC
        @ptype modified: datetime or None
        @return: formatted date or empty string
        @rtype: unicode
        """
        if modified is not None:
            return modified.strftime("%Y-%m-%d{0}%H:%M:%S.%fZ".format(sep))
        return u""

def _get_loggers():
    """Return list of Logger classes."""
    from .. import loader
    modules = loader.get_package_modules('logger')
    return list(loader.get_plugins(modules, [_Logger]))


LoggerClasses = _get_loggers()
LoggerNames = [x.LoggerName for x in LoggerClasses]
LoggerKeys = ", ".join(repr(x) for x in LoggerNames)
