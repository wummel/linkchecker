# -*- coding: iso-8859-1 -*-
"""Find link tags in HTML text"""
# Copyright (C) 2001-2004  Bastian Kleineidam
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
import linkcheck.strformat
import linkcheck.linkname
import linkcheck.log


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
css_url_re = re.compile(r"url\((?P<url>[^\)]+)\)")

class TagFinder (object):
    """Base class storing HTML parse messages in a list.
       TagFinder instances are to be used as HtmlParser handlers.
    """

    def __init__ (self, content):
        """store content in buffer"""
        self.content = content
        # warnings and errors during parsing
        self.parse_info = []
        # parser object will be initialized when it is used as
        # a handler object
        self.parser = None

    def _errorfun (self, msg, name):
        """append msg to error list"""
        self.parse_info.append("%s at line %d col %d: %s" % \
            (name, self.parser.last_lineno(), self.parser.last_column(), msg))

    def warning (self, msg):
        """signal a filter/parser warning"""
        self._errorfun(msg, "warning")

    def error (self, msg):
        """signal a filter/parser error"""
        self._errorfun(msg, "error")

    def fatal_error (self, msg):
        """signal a fatal filter/parser error"""
        self._errorfun(msg, "fatal error")


class MetaRobotsFinder (TagFinder):
    """class for finding robots.txt meta values in HTML"""

    def __init__ (self, content):
        """store content in buffer and initialize flags"""
        super(MetaRobotsFinder, self).__init__(content)
        self.follow = True
        self.index = True


    def start_element (self, tag, attrs):
        """search for meta robots.txt "nofollow" and "noindex" flags"""
        if tag == 'meta':
            if attrs.get('name') == 'robots':
                val = attrs.get('content', '').lower().split(',')
                self.follow = 'nofollow' not in val
                self.index = 'noindex' not in val


class LinkFinder (TagFinder):
    """find a list of links. After parsing, the urls
    will have a list of parsed links entries with the format
    (url, lineno, column, name, base)
    """

    def __init__ (self, content, tags=None):
        """store content in buffer and initialize url list"""
        super(LinkFinder, self).__init__(content)
        if tags is None:
            self.tags = LinkTags
        else:
            self.tags = tags
        self.urls = []

    def start_element (self, tag, attrs):
        """search for links and store found urls in url list"""
        linkcheck.log.debug(linkcheck.LOG_CHECK, "LinkFinder tag %s attrs %s",
                            tag, attrs)
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "line %d col %d old line %d old col %d",
                            self.parser.lineno(), self.parser.column(),
                         self.parser.last_lineno(), self.parser.last_column())
        tagattrs = self.tags.get(tag, [])
        tagattrs.extend(self.tags.get(None, []))
        for attr in tagattrs:
            if attr in attrs:
                # name of this link
                if tag == 'a' and attr == 'href':
                    name = linkcheck.strformat.unquote(attrs.get('title', ''))
                    if not name:
                        name = linkcheck.linkname.href_name(
                                            self.content[self.parser.pos():])
                elif tag == 'img':
                    name = linkcheck.strformat.unquote(attrs.get('alt', ''))
                    if not name:
                        name = linkcheck.strformat.unquote(
                                                     attrs.get('title', ''))
                else:
                    name = ""
                # possible codebase
                if tag in ('applet', 'object'):
                    base = linkcheck.strformat.unquote(attrs.get('codebase'))
                else:
                    base = ""
                value = linkcheck.strformat.unquote(attrs[attr])
                # add link to url list
                self.add_link(tag, attr, value, name, base)

    def add_link (self, tag, attr, url, name, base):
        """add given url data to url list"""
        urls = []
        # look for meta refresh
        if tag == 'meta':
            mo = _refresh_re.match(url)
            if mo:
                urls.append(mo.group("url"))
        elif attr == 'style':
            for mo in css_url_re.finditer(url):
                urls.append(mo.group("url"))
        else:
            urls.append(url)
        if not urls:
            # no url found
            return
        for u in urls:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
              "LinkParser add link %s %s %s %s %s", tag, attr, u, name, base)
            self.urls.append((u, self.parser.last_lineno(),
                              self.parser.last_column(), name, base))
