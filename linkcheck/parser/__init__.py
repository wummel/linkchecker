# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2004  Bastian Kleineidam
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
"""Fast HTML parser module written in C with the following features:

1. Reentrant
   
   As soon as any HTML string data is available, we try to feed it
   to the HTML parser. This means that the parser has to scan possible
   incomplete data, recognizing as much as it can. Incomplete trailing
   data is saved for subsequent calls (or it is just flushed away with the
   flush() function).
   A reset() brings the parser back to its initial state, throwing away all
   buffered data.

2. Coping with HTML syntax errors
   
   The parser recognizes as much as it can and passes the rest
   of the data as TEXT tokens.
   The scanner only passes complete recognized HTML syntax elements to
   the parser. Invalid syntax elements are passed as TEXT. This way we do
   not need the bison error recovery.
   Incomplete data is rescanned the next time the parser calls yylex() or
   when it is being flush()ed.
   
   The following syntax errors will be recognized correctly:
   
   a) missing quotes around attribute values
   b) "</...>" end tags in script modus
   c) missing ">" in tags
   d) invalid tag names
   e) invalid characters inside tags or tag attributes
   
   Additionally the parser has the following features:
   
   a) NULL bytes are changed into spaces
   b) <!-- ... --> inside a <script> or <style> are not treated as
      comments, so you can safely turn on the comment delete rule

3. Speed
   
   The FLEX code has options to generate a large but fast scanner.
   The parser ignores forbidden or unnecessary HTML end tags.
   The parser converts tag and attribute names to lower case for easier
   matching.
   The parser quotes all attribute values with minimal necessity (this is
   not standard compliant, but who cares when the browsers understand it).
   The Python memory management interface is being used.

"""

__version__ = "$Revision$"[11:-2]
__date__    = "$Date$"[7:-2]

import re
import htmlentitydefs


def _resolve_entity (mo):
    """resolve one &#XXX; entity"""
    # convert to number
    ent = mo.group()
    num = mo.group("num")
    if ent.startswith('&#x'):
        radix = 16
    else:
        radix = 10
    num = int(num, radix)
    # check 7-bit ASCII char range
    if 0<=num<=127:
        return chr(num)
    # not in range
    return ent


def resolve_entities (s):
    """resolve entities in 7-bit ASCII range to eliminate obfuscation"""
    return re.sub(r'(?i)&#x?(?P<num>\d+);', _resolve_entity, s)

entities = htmlentitydefs.entitydefs.items()

UnHtmlTable = [("&"+x[0]+";", x[1]) for x in entities]
# order matters!
UnHtmlTable.sort()
UnHtmlTable.reverse()

def applyTable (table, s):
    "apply a table of replacement pairs to str"
    for mapping in table:
        s = s.replace(mapping[0], mapping[1])
    return s


def resolve_html_entities (s):
    """resolve html entites in s and return result"""
    return applyTable(UnHtmlTable, s)


def strip_quotes (s):
    """remove possible double or single quotes"""
    if (s.startswith("'") and s.endswith("'")) or \
       (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s

