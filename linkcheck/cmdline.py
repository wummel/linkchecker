# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2012 Bastian Kleineidam
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
Utility functions suitable for command line clients.
"""
import sys
import optparse
from . import fileutil, ansicolor, strformat, checker
from .director import console
from .decorators import notimplemented

def print_version(exit_code=0):
    """Print the program version and exit."""
    console.print_version()
    sys.exit(exit_code)


def print_usage (msg, exit_code=2):
    """Print a program msg text to stderr and exit."""
    program = sys.argv[0]
    print >> console.stderr, _("Error: %(msg)s") % {"msg": msg}
    print >> console.stderr, _("Execute '%(program)s -h' for help") % {"program": program}
    sys.exit(exit_code)


class LCHelpFormatter (optparse.IndentedHelpFormatter, object):
    """Help formatter indenting paragraph-wise."""

    def __init__ (self):
        """Set current console width for this formatter."""
        width = ansicolor.get_columns(sys.stdout)
        super(LCHelpFormatter, self).__init__(width=width)

    def format_option (self, option):
        """Customized help display with indentation."""
        # The help for each option consists of two parts:
        #   * the opt strings and metavars
        #     eg. ("-x", or "-fFILENAME, --file=FILENAME")
        #   * the user-supplied help string
        #     eg. ("turn on expert mode", "read data from FILENAME")

        # If possible, we write both of these on the same line:
        #   -x      turn on expert mode

        # But if the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in if it fit on the first line.
        #   -fFILENAME, --file=FILENAME
        #           read data from FILENAME
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else:                       # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            text = strformat.wrap(option.help, self.help_width)
            help_lines = text.splitlines()
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                           for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)


class LCOptionParser (optparse.OptionParser, object):
    """Option parser with custom help text layout."""

    def __init__ (self, err_exit_code=2):
        """Initializing using our own help formatter class."""
        super(LCOptionParser, self).__init__(formatter=LCHelpFormatter())
        self.err_exit_code = err_exit_code

    def error (self, msg):
        """Print usage info and given message."""
        print_usage(msg, exit_code=self.err_exit_code)

    @notimplemented
    def get_usage (self):
        """Print usage text."""
        pass

    def print_help_msg (self, s, out):
        """Print a help message to stdout."""
        s = console.encode(s)
        if fileutil.is_tty(out):
            strformat.paginate(s)
        else:
            print >>out, s
        sys.exit(0)

    @notimplemented
    def print_help (self, file=None):
        """Print help text to given file."""
        pass


def aggregate_url (aggregate, url, err_exit_code=2):
    """Append given commandline URL to input queue."""
    get_url_from = checker.get_url_from
    url = checker.guess_url(url)
    url_data = get_url_from(url, 0, aggregate, extern=(0, 0))
    aggregate.urlqueue.put(url_data)
