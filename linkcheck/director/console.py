# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2008 Bastian Kleineidam
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
Helpers for console output.
"""
import sys
import os
import codecs
import traceback
from .. import i18n, configuration

# Output to stdout and stderr, encoded with the default encoding
stderr = codecs.getwriter(i18n.default_encoding)(sys.stderr, errors="ignore")
stdout = codecs.getwriter(i18n.default_encoding)(sys.stdout, errors="ignore")


class StatusLogger (object):
    """Standard status logger object simulating a file object. Default
    output is stderr."""

    def __init__ (self, fd=stderr):
        self.fd = fd

    def write (self, msg):
        self.fd.write(msg)

    def writeln (self, msg):
        self.fd.write(u"%s%s" % (msg, unicode(os.linesep)))

    def flush (self):
        self.fd.flush()


def internal_error (out=stderr):
    """Print internal error message (output defaults to stderr)."""
    print >> out, os.linesep
    print >> out, _("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
- the URL or file you are testing
- your commandline arguments and/or configuration.
- the output of a debug run with option "-Dall" of the executed command
- the system information below.

Not disclosing some of the information above due to privacy reasons is ok.
I will try to help you nonetheless, but you have to give me something
I can work with ;) .
""") % configuration.Email
    etype, value = sys.exc_info()[:2]
    print >> out, etype, value
    traceback.print_exc()
    print_app_info()
    print >> out, os.linesep, \
            _("******** LinkChecker internal error, over and out ********")


def print_app_info (out=stderr):
    """Print system and application info (output defaults to stderr)."""
    print >> out, _("System info:")
    print >> out, configuration.App
    print >> out, _("Python %(version)s on %(platform)s") % \
                    {"version": sys.version, "platform": sys.platform}
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> out, key, "=", repr(value)


def print_version (out=stdout):
    """Print the program version (output defaults to stdout)."""
    print >> out, configuration.AppInfo
