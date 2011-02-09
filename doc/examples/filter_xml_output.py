#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Bastian Kleineidam
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
Example to filter XML output.
Call with XML output filename as first argument.
Prints filtered result on standard output.
"""
import sys
from xml.etree.ElementTree import parse


def main (args):
    filename = args[0]
    with open(filename) as fd:
        tree = parse(fd)
        filter_tree(tree)
        tree.write(sys.stdout, encoding='utf-8')


def filter_tree(tree):
    """Filter all 401 errors."""
    to_remove = []
    for elem in tree.findall('urldata'):
        valid = elem.find('valid')
        if valid is not None and valid.text == '0' and \
           valid.attrib.get('result', '').startswith('401'):
            to_remove.append(elem)
    root = tree.getroot()
    for elem in to_remove:
        root.remove(elem)


if __name__ == '__main__':
    main(sys.argv[1:])
