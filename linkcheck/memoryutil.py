# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012 Bastian Kleineidam
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
Memory utilities.
"""
import sys
from . import strformat
from .fileutil import get_temp_file

# Message to display when meliae package is not installed
MemoryDebugMsg = strformat.format_feature_warning(module=u'meliae',
            feature=u'memory debugging',
            url=u'https://launchpad.net/meliae')


def write_memory_dump():
    """Dump memory to a temporary filename with the meliae package.
    @return: JSON filename where memory dump has been written to
    @rtype: string
    """
    from meliae import scanner
    fo, filename = get_temp_file(mode='wb', suffix='.json', prefix='lcdump_')
    try:
        scanner.dump_all_objects(fo)
    finally:
        fo.close()
    return filename


def print_memory_dump(filename, out=sys.stdout):
    """Print a memory dump to given output stream.
    @param filename: memory dump file
    @ptype filename: string
    @param out: output stream, default: stdout
    @ptype out: open file object
    """
    from meliae import loader
    om = loader.load(filename)
    print >>out, om.summarize()
