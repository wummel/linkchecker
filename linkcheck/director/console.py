# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
Helpers for console output.
"""
from __future__ import print_function
import sys
import os
import time
from .. import i18n, configuration, strformat, better_exchook2

# Output to stdout and stderr, encoded with the default encoding
stderr = i18n.get_encoded_writer(out=sys.stderr)
stdout = i18n.get_encoded_writer()


def encode (text):
    """Encode text with default encoding if its Unicode."""
    if isinstance(text, unicode):
        return text.encode(i18n.default_encoding, 'ignore')
    return text


class StatusLogger (object):
    """Standard status logger. Default output is stderr."""

    def __init__ (self, fd=stderr):
        """Save file descriptor for logging."""
        self.fd = fd

    def log_status (self, checked, in_progress, queue, duration, num_urls):
        """Write status message to file descriptor."""
        msg = _n("%2d thread active", "%2d threads active", in_progress) % \
          in_progress
        self.write(u"%s, " % msg)
        msg = _n("%5d link queued", "%5d links queued", queue) % queue
        self.write(u"%s, " % msg)
        msg = _n("%4d link", "%4d links", checked) % checked
        self.write(u"%s" % msg)
        msg = _n("%3d URL", "%3d URLs", num_urls) % num_urls
        self.write(u" in %s checked, " % msg)
        msg = _("runtime %s") % strformat.strduration_long(duration)
        self.writeln(msg)
        self.flush()

    def write (self, msg):
        """Write message to file descriptor."""
        self.fd.write(msg)

    def writeln (self, msg):
        """Write status message and line break to file descriptor."""
        self.fd.write(u"%s%s" % (msg, unicode(os.linesep)))

    def flush (self):
        """Flush file descriptor."""
        self.fd.flush()


def internal_error (out=stderr, etype=None, evalue=None, tb=None):
    """Print internal error message (output defaults to stderr)."""
    print(os.linesep, file=out)
    print(_("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at %s
and include the following information:
- the URL or file you are testing
- the system information below

When using the commandline client:
- your commandline arguments and any custom configuration files.
- the output of a debug run with option "-Dall"

Not disclosing some of the information above due to privacy reasons is ok.
I will try to help you nonetheless, but you have to give me something
I can work with ;) .
""") % configuration.SupportUrl, file=out)
    if etype is None:
        etype = sys.exc_info()[0]
    if evalue is None:
        evalue = sys.exc_info()[1]
    if tb is None:
        tb = sys.exc_info()[2]
    better_exchook2.better_exchook(etype, evalue, tb, out=out)
    print_app_info(out=out)
    print_proxy_info(out=out)
    print_locale_info(out=out)
    print(os.linesep,
      _("******** LinkChecker internal error, over and out ********"), file=out)


def print_env_info (key, out=stderr):
    """If given environment key is defined, print it out."""
    value = os.getenv(key)
    if value is not None:
        print(key, "=", repr(value), file=out)


def print_proxy_info (out=stderr):
    """Print proxy info."""
    for key in ("http_proxy", "ftp_proxy", "no_proxy"):
        print_env_info(key, out=out)


def print_locale_info (out=stderr):
    """Print locale info."""
    for key in ("LANGUAGE", "LC_ALL", "LC_CTYPE", "LANG"):
        print_env_info(key, out=out)
    print(_("Default locale:"), i18n.get_locale(), file=out)

# Environment variables influencing the interpreter execution
# See python(1) man page.
PYTHON_ENV_VARS = (
    'PYTHONHOME',
    'PYTHONPATH',
    'PYTHONSTARTUP',
    'PYTHONY2K',
    'PYTHONOPTIMIZE',
    'PYTHONDEBUG',
    'PYTHONDONTWRITEBYTECODE',
    'PYTHONINSPECT',
    'PYTHONIOENCODING',
    'PYTHONNOUSERSITE',
    'PYTHONUNBUFFERED',
    'PYTHONVERBOSE',
    'PYTHONWARNINGS',
    'PYTHONHASHSEED',
)
def print_app_info (out=stderr):
    """Print system and application info (output defaults to stderr)."""
    print(_("System info:"), file=out)
    print(configuration.App, file=out)
    print(_("Released on:"), configuration.ReleaseDate, file=out)
    print(_("Python %(version)s on %(platform)s") %
                    {"version": sys.version, "platform": sys.platform}, file=out)
    for key in PYTHON_ENV_VARS:
        print_env_info(key, out=out)
    print(configuration.get_modules_info(), file=out)
    stime = strformat.strtime(time.time())
    print(_("Local time:"), stime, file=out)
    print(_("sys.argv:"), sys.argv, file=out)


def print_version (out=stdout):
    """Print the program version (output defaults to stdout)."""
    print(configuration.App, _("released"),
          configuration.ReleaseDate, file=out)
    print(configuration.Copyright, file=out)
