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
    'a':        [u'href'],
    'applet':   [u'archive', u'src'],
    'area':     [u'href'],
    'bgsound':  [u'src'],
    'blockquote': [u'cite'],
    'body':     [u'background'],
    'del':      [u'cite'],
    'embed':    [u'pluginspage', u'src'],
    'form':     [u'action'],
    'frame':    [u'src', u'longdesc'],
    'head':     [u'profile'],
    'iframe':   [u'src', u'longdesc'],
    'ilayer':   [u'background'],
    'img':      [u'src', u'lowsrc', u'longdesc', u'usemap'],
    'input':    [u'src', u'usemap'],
    'ins':      [u'cite'],
    'isindex':  [u'action'],
    'layer':    [u'background', u'src'],
    'link':     [u'href'],
    'meta':     [u'content'],
    'object':   [u'classid', u'data', u'archive', u'usemap'],
    'q':        [u'cite'],
    'script':   [u'src', u'for'],
    'table':    [u'background'],
    'td':       [u'background'],
    'th':       [u'background'],
    'tr':       [u'background'],
    'xmp':      [u'href'],
    None:       [u'style'],
}

# matcher for <meta http-equiv=refresh> tags
refresh_re = re.compile(ur"(?i)^\d+;\s*url=(?P<url>.+)$")
css_url_re = re.compile(ur"url\((?P<url>[^\)]+)\)")

class TagFinder (object):
    """Base class storing HTML parse messages in a list.
       TagFinder instances are to be used as HtmlParser handlers.
    """

    def __init__ (self, content):
        """store content in buffer"""
        super(TagFinder, self).__init__()
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
        linkcheck.log.debug(linkcheck.LOG_CHECK, "meta robots finder")


    def start_element (self, tag, attrs):
        """search for meta robots.txt "nofollow" and "noindex" flags"""
        if tag == 'meta':
            if attrs.get('name') == 'robots':
                val = attrs.get('content', u'').lower().split(u',')
                self.follow = u'nofollow' not in val
                self.index = u'noindex' not in val


class LinkFinder (TagFinder):
    """Find a list of links. After parsing, self.urls
    will be a list of parsed links entries with the format
    (url, lineno, column, name, codebase)
    """

    def __init__ (self, content, tags=None):
        """store content in buffer and initialize URL list"""
        super(LinkFinder, self).__init__(content)
        if tags is None:
            self.tags = LinkTags
        else:
            self.tags = tags
        self.urls = []
        self.base_ref = u''
        linkcheck.log.debug(linkcheck.LOG_CHECK, "link finder")

    def start_element (self, tag, attrs):
        """search for links and store found URLs in a list"""
        linkcheck.log.debug(linkcheck.LOG_CHECK, "LinkFinder tag %s attrs %s",
                            tag, attrs)
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "line %d col %d old line %d old col %d",
                            self.parser.lineno(), self.parser.column(),
                         self.parser.last_lineno(), self.parser.last_column())
        if tag == "base" and not self.base_ref:
            self.base_ref = attrs.get("href", u'')
        tagattrs = self.tags.get(tag, [])
        tagattrs.extend(self.tags.get(None, []))
        for attr in tagattrs:
            if attr not in attrs:
                continue
            # name of this link
            name = self.get_link_name(tag, attrs, attr)
            # possible codebase
            if tag in ('applet', 'object'):
                codebase = linkcheck.strformat.unquote(
                                                  attrs.get('codebase', u''))
            else:
                codebase = u''
            value = linkcheck.strformat.unquote(attrs[attr])
            # add link to url list
            self.add_link(tag, attr, value, name, codebase)
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "LinkFinder finished tag %s", tag)

    def get_link_name (self, tag, attrs, attr):
        """Parse attrs for link name. Return name of link"""
        if tag == 'a' and attr == 'href':
            name = linkcheck.strformat.unquote(attrs.get('title', u''))
            if not name:
                data = self.content[self.parser.pos():]
                data = data.decode(self.parser.encoding, "ignore")
                name = linkcheck.linkname.href_name(data)
        elif tag == 'img':
            name = linkcheck.strformat.unquote(attrs.get('alt', u''))
            if not name:
                name = linkcheck.strformat.unquote(attrs.get('title', u''))
        else:
            name = u""
        return name

    def add_link (self, tag, attr, url, name, base):
        """add given url data to url list"""
        urls = []
        # look for meta refresh
        if tag == 'meta':
            mo = refresh_re.match(url)
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
            assert isinstance(tag, unicode), tag
            assert isinstance(attr, unicode), attr
            assert isinstance(u, unicode), u
            assert isinstance(name, unicode), name
            assert isinstance(base, unicode), base
            linkcheck.log.debug(linkcheck.LOG_CHECK,
              u"LinkParser add link %s %s %s %s %s", tag, attr, u, name, base)
            self.urls.append((u, self.parser.last_lineno(),
                              self.parser.last_column(), name, base))
