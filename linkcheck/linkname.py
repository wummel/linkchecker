# -*- coding: iso-8859-1 -*-
"""parse name of common link types"""
# Copyright (C) 2001-2005  Bastian Kleineidam
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

import re
import linkcheck
import linkcheck.HtmlParser
import linkcheck.strformat


imgtag_re = re.compile(r"(?i)\s+alt\s*=\s*"+\
                       r"""(?P<name>("[^"\n]*"|'[^'\n]*'|[^\s>]+))""")
img_re = re.compile(r"""(?i)<\s*img\s+("[^"\n]*"|'[^'\n]*'|[^>])+>""")
endtag_re = re.compile(r"""(?i)</a\s*>""")

def _unquote (txt):
    """resolve entities and markup from txt"""
    return linkcheck.HtmlParser.resolve_entities(
                  linkcheck.strformat.remove_markup(txt))

def image_name (txt):
    """return the alt part of the first <img alt=""> tag in txt"""
    mo = imgtag_re.search(txt)
    if mo:
        name = linkcheck.strformat.unquote(mo.group('name').strip())
        return  _unquote(name)
    return u''


def href_name (txt):
    """return the name part of the first <a href="">name</a> link in txt"""
    name = u""
    endtag = endtag_re.search(txt)
    if not endtag:
        return name
    name = txt[:endtag.start()]
    if img_re.search(name):
        return image_name(name)
    return _unquote(name)
