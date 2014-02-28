# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2014 Bastian Kleineidam
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
Parse names of title tags and link types.
"""

import re
from .. import HtmlParser, strformat


imgtag_re = re.compile(r"(?i)\s+alt\s*=\s*"+\
                       r"""(?P<name>("[^"\n]*"|'[^'\n]*'|[^\s>]+))""")
img_re = re.compile(r"""(?i)<\s*img\s+("[^"\n]*"|'[^'\n]*'|[^>])+>""")


def endtag_re (tag):
    """Return matcher for given end tag"""
    return re.compile(r"(?i)</%s\s*>" % tag)

a_end_search = endtag_re("a").search
title_end_search = endtag_re("title").search


def _unquote (txt):
    """Resolve entities and remove markup from txt."""
    return HtmlParser.resolve_entities(strformat.remove_markup(txt))


def image_name (txt):
    """Return the alt part of the first <img alt=""> tag in txt."""
    mo = imgtag_re.search(txt)
    if mo:
        name = strformat.unquote(mo.group('name').strip())
        return  _unquote(name)
    return u''


def href_name (txt):
    """Return the name part of the first <a href="">name</a> link in txt."""
    name = u""
    endtag = a_end_search(txt)
    if not endtag:
        return name
    name = txt[:endtag.start()]
    if img_re.search(name):
        return image_name(name)
    return _unquote(name)


def title_name (txt):
    """Return the part of the first <title>name</title> in txt."""
    name = u""
    endtag = title_end_search(txt)
    if not endtag:
        return name
    name = txt[:endtag.start()]
    return _unquote(name)
