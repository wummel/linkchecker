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
   data is saved for subsequent callsm, or it is just flushed into the
   output buffer with the flush() function.
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
      comments but as DATA

3. Speed

   The FLEX code has options to generate a large but fast scanner.
   The parser ignores forbidden or unnecessary HTML end tags.
   The parser converts tag and attribute names to lower case for easier
   matching.
   The parser quotes all attribute values.
   Python memory management interface is used.

4. Character encoding aware

   The parser itself is not encoding aware, but all the output are
   always Python Unicode strings.
"""

import re
import codecs
import htmlentitydefs


def _resolve_ascii_entity (mo):
    """Helper function for resolve_entities to resolve one &#XXX;
       entity if it is an ASCII character. Else leave as is.
       Input is a match object with a "num" group matched.
    """
    # convert to number
    ent = mo.group()
    num = mo.group("num")
    if ent.startswith('&#x'):
        radix = 16
    else:
        radix = 10
    num = int(num, radix)
    # check 7-bit ASCII char range
    if 0 <= num <= 127:
        return unicode(chr(num))
    # not in range
    return ent


_num_re = re.compile(ur'(?i)&#x?(?P<num>\d+);')
def resolve_ascii_entities (s):
    """resolve entities in 7-bit ASCII range to eliminate obfuscation"""
    return _num_re.sub(_resolve_ascii_entity, s)


def _resolve_html_entity (mo):
    """resolve html entity, helper function for resolve_html_entities"""
    ent = mo.group("entity")
    s = mo.group()
    entdef = htmlentitydefs.entitydefs.get(ent)
    if entdef is None:
        return s
    # note: entdef is latin-1 encoded
    return entdef.decode("iso8859-1")


_entity_re = re.compile(ur'(?i)&(?P<entity>[a-z]+);')
def resolve_html_entities (s):
    """resolve html entites in s and return result"""
    return _entity_re.sub(_resolve_html_entity, s)


def resolve_entities (s):
    """resolve both html and 7-bit ASCII entites in s and return result"""
    s = resolve_ascii_entities(s)
    return resolve_html_entities(s)


def strip_quotes (s):
    """remove possible double or single quotes"""
    if len(s) >= 2 and \
       ((s.startswith("'") and s.endswith("'")) or \
        (s.startswith('"') and s.endswith('"'))):
        return s[1:-1]
    return s


_encoding_ro = re.compile(r"charset=(?P<encoding>[-0-9a-zA-Z]+)")

def set_encoding (self, tag, attrs):
    """Set document encoding for given parser. Tag must be a meta tag."""
    if tag != u'meta':
        return
    if attrs.get('http-equiv', u'').lower() == u"content-type":
        content = attrs.get('content', u'')
        mo = _encoding_ro.search(content)
        if mo:
            encoding = mo.group("encoding").encode("ascii")
            try:
                encoding = encoding.encode("ascii")
                codecs.lookup(encoding)
                self.encoding = encoding
            except LookupError:
                # ignore unknown encodings
                pass


def set_doctype (self, doctype):
    if u"XHTML" in doctype:
        self.doctype = "XHTML"

