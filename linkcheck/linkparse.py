# -*- coding: iso-8859-1 -*-
# Copyright (C) 2001-2003  Bastian Kleineidam
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

import re, StringUtil, linkname
from debug import *
from linkcheck.parser.htmllib import HtmlParser

# ripped mainly from HTML::Tagset.pm
LinkTags = {
    'a':        ['href'],
    'applet':   ['archive', 'src'],
    'area':     ['href'],
    'bgsound':  ['src'],
    'blockquote': ['cite'],
    'body':     ['background'],
    'del':      ['cite'],
    'embed':    ['pluginspage', 'src'],
    'form':     ['action'],
    'frame':    ['src', 'longdesc'],
    'head':     ['profile'],
    'iframe':   ['src', 'longdesc'],
    'ilayer':   ['background'],
    'img':      ['src', 'lowsrc', 'longdesc', 'usemap'],
    'input':    ['src', 'usemap'],
    'ins':      ['cite'],
    'isindex':  ['action'],
    'layer':    ['background', 'src'],
    'link':     ['href'],
    'meta':     ['content'],
    'object':   ['classid', 'data', 'archive', 'usemap'],
    'q':        ['cite'],
    'script':   ['src', 'for'],
    'table':    ['background'],
    'td':       ['background'],
    'th':       ['background'],
    'tr':       ['background'],
    'xmp':      ['href'],
    None:       ['style'],
}

# matcher for <meta http-equiv=refresh> tags
_refresh_re = re.compile(r"(?i)^\d+;\s*url=(?P<url>.+)$")
_style_background_re = re.compile(r"background-image:\s*url\((?P<url>.+?)\)")

class LinkParser (HtmlParser):
    """Parse the content for a list of links. After parsing, the urls
    will have a list of parsed links entries with the format
    (url, lineno, column, name, base)
    """

    def __init__ (self, content, tags=LinkTags):
        super(LinkParser, self).__init__()
        self.content = content
        self.tags = tags
        self.urls = []
        # warnings and errors during parsing
        self.parse_info = []
        self.feed(self.content)
        debug(HURT_ME_PLENTY, "flushing")
        self.flush()


    def startElement (self, tag, attrs):
        debug(NIGHTMARE, "LinkParser tag", tag, "attrs", attrs)
        debug(NIGHTMARE, "line", self.lineno(), "col", self.column(),
              "old line", self.last_lineno(), "old col", self.last_column())
        tagattrs = self.tags.get(tag, [])
        tagattrs.extend(self.tags.get(None, []))
        for attr in tagattrs:
            if attr in attrs:
                # name of this link
                if tag=='a' and attr=='href':
                    name = StringUtil.unquote(attrs.get('title', ''))
                    if not name:
                        name = linkname.href_name(self.content[self.pos():])
                elif tag=='img':
                    name = StringUtil.unquote(attrs.get('alt', ''))
                    if not name:
                        name = StringUtil.unquote(attrs.get('title', ''))
                else:
                    name = ""
                # possible codebase
                if tag in ('applet', 'object'):
                    base = StringUtil.unquote(attrs.get('codebase'))
                else:
                    base = ""
                value = StringUtil.unquote(attrs[attr])
                # add link to url list
                self.addLink(tag, attr, value, name, base)


    def addLink (self, tag, attr, url, name, base):
        # look for meta refresh
        if tag=='meta':
            mo = _refresh_re.match(url)
            if mo:
                url = mo.group("url")
            else:
                # only meta refresh has an url, so return
                return
        elif attr=='style':
            mo = _style_background_re.search(url)
            if mo:
               url = mo.group("url")
            else:
                return
        debug(NIGHTMARE, "LinkParser add link", tag, attr, url, name, base)
        self.urls.append((url, self.last_lineno(), self.last_column(),
                          name, base))


    def _errorfun (self, msg, name):
        """append msg to error list"""
        self.parse_info.append("%s at line %d col %d: %s" % \
                (name, self.last_lineno(), self.last_column(), msg))

    def error (self, msg):
        """signal a filter/parser error"""
        self._errorfun(msg, "error")

    def warning (self, msg):
        """signal a filter/parser warning"""
        self._errorfun(msg, "warning")

    def fatalError (self, msg):
        """signal a fatal filter/parser error"""
        self._errorfun(msg, "fatal error")

