#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011-2014 Bastian Kleineidam
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
Parse HTML given as file parameter or piped to stdin.
"""
import sys
import os
sys.path.append(os.getcwd())
import linkcheck.HtmlParser.htmlsax
import linkcheck.HtmlParser.htmllib


def main (text):
    parser = linkcheck.HtmlParser.htmlsax.parser()
    handler = linkcheck.HtmlParser.htmllib.HtmlPrinter()
    parser.handler = handler
    # debug lexer
    #parser.debug(1)
    parser.feed(text)
    parser.flush()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        text = sys.stdin.read()
    else:
        filename = sys.argv[1]
        with open(filename) as fp:
            text = fp.read()
    main(text)
