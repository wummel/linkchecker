# -*- coding: iso-8859-1 -*-
"""XML utility functions"""
# Copyright (C) 2003-2004  Bastian Kleineidam
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

__version__ = "$Revision$"[11:-2]
__date__    = "$Date$"[7:-2]

from xml.sax.saxutils import escape, unescape

attr_entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
}


def xmlquote (s):
    """quote characters for XML"""
    return escape(s)


def xmlquoteattr (s):
    """quote XML attribute, ready for inclusion with double quotes"""
    return escape(s, attr_entities)


def xmlunquote (s):
    """unquote characters from XML"""
    return unescape(s)


def xmlunquoteattr (s):
    """unquote attributes from XML"""
    return unescape(s, attr_entities)

