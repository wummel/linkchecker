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
Utility functions suitable for command line clients.
"""
from __future__ import print_function
import sys
import argparse
from . import checker, fileutil, strformat, plugins
from .director import console


class LCArgumentParser(argparse.ArgumentParser):
    """Custom argument parser to format help text."""

    def print_help(self, file=sys.stdout):
        """Print a help message to stdout."""
        msg = console.encode(self.format_help())
        if fileutil.is_tty(file):
            strformat.paginate(msg)
        else:
            print(msg, file=file)


def print_version(exit_code=0):
    """Print the program version and exit."""
    console.print_version()
    sys.exit(exit_code)


def print_plugins(folders, exit_code=0):
    """Print available plugins and exit."""
    modules = plugins.get_plugin_modules(folders)
    pluginclasses = sorted(plugins.get_plugin_classes(modules), key=lambda x: x.__name__)

    for pluginclass in pluginclasses:
        print(pluginclass.__name__)
        doc = strformat.wrap(pluginclass.__doc__, 80)
        print(strformat.indent(doc))
        print()
    sys.exit(exit_code)


def print_usage (msg, exit_code=2):
    """Print a program msg text to stderr and exit."""
    program = sys.argv[0]
    print(_("Error: %(msg)s") % {"msg": msg}, file=console.stderr)
    print(_("Execute '%(program)s -h' for help") % {"program": program}, file=console.stderr)
    sys.exit(exit_code)


def aggregate_url (aggregate, url, err_exit_code=2):
    """Append given commandline URL to input queue."""
    get_url_from = checker.get_url_from
    url = checker.guess_url(url)
    url_data = get_url_from(url, 0, aggregate, extern=(0, 0))
    aggregate.urlqueue.put(url_data)
