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
Output logging support for different formats.
"""

import locale
import sys
import os
import datetime

import linkcheck.strformat
import linkcheck.i18n

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
    dltime=_("D/L Time"),
    dlsize=_("D/L Size"),
    checktime=_("Check Time"),
    url=_("URL"),
)
del _

class Logger (object):
    """
    Basic logger class enabling logging of checked urls.
    """

    def __init__ (self, **args):
        """
        Initialize a logger, looking for part restrictions in kwargs.
        """
        # what log parts should be in output
        self.logparts = None # log all parts
        if args.has_key('parts'):
            if "all" not in args['parts']:
                # only log given parts
                self.logparts = args['parts']
        # number of spaces before log parts for alignment
        self.logspaces = {}
        # maximum indent of spaces for alignment
        self.max_indent = 0
        # number of logged urls
        self.number = 0
        # number of encountered errors
        self.errors = 0
        # number of encountered warningss
        self.warnings = 0
        # encoding of output
        default = linkcheck.i18n.default_encoding
        self.output_encoding = args.get("encoding", default)

    def init_fileoutput (self, args):
        """
        Initialize self.fd file descriptor from args.
        """
        if args.get('fileoutput'):
            filename = args['filename']
            path = os.path.dirname(filename)
            if path and not os.path.isdir(path):
                os.makedirs(path)
            self.fd = file(filename, "wb")
            self.close_fd = True
        elif args.has_key('fd'):
            self.fd = args['fd']
            self.close_fd = False
        else:
            self.fd = sys.stdout
            self.close_fd = False

    def close_fileoutput (self):
        """
        Flush and close the file output denoted by self.fd.
        """
        self.flush()
        if self.close_fd:
            self.fd.close()
        self.fd = None

    def encode (self, s):
        """
        Encode string with configured output encoding. Wrong encoded
        characters are replaced.

        @param s: string to encode
        @type s: unicode
        @return: encoded string
        @rtype: string
        """
        if not isinstance(s, unicode):
            raise ValueError, "tried to encode non-unicode string %r" % s
        return s.encode(self.output_encoding, "replace")

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
        return linkcheck.strformat.wrap(text, width,
                            subsequent_indent=" "*self.max_indent,
                            initial_indent=" "*self.max_indent).lstrip()

    def write (self, s, **args):
        """
        Write string to output descriptor.
        """
        if self.fd is None:
            raise ValueError, "write to non-file"
        self.fd.write(self.encode(s), **args)

    def writeln (self, s=u"", **args):
        """
        Write string to output descriptor plus a newline.
        """
        self.write(s)
        self.write(unicode(os.linesep), **args)

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
        return _(Fields[name])

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
        values = [self.part(x) for x in parts]
        # maximum indent for localized log part names
        self.max_indent = max([len(x) for x in values])+1
        for key in parts:
            numspaces = (self.max_indent - len(self.part(key)))
            self.logspaces[key] = u" " * numspaces

    def log_filter_url (self, url_data, do_print):
        """
        Log a new url with this logger if do_filter is True. Else
        only update accounting data
        """
        self.number += 1
        if not url_data.valid:
            self.errors += 1
        self.warnings += len(url_data.warnings)
        if do_print:
            self.log_url(url_data)

    def log_url (self, url_data):
        """
        Log a new url with this logger.
        """
        raise NotImplementedError, "abstract function"

    def end_output (self):
        """
        End of output, used for cleanup (eg output buffer flushing).
        """
        raise NotImplementedError, "abstract function"

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
            except IOError:
                pass
