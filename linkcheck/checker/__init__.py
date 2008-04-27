# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
"""
Main functions for link checking.
"""

import os
import cgi
import logging
import urllib
import linkcheck.httplib2
import linkcheck.dns.exception
from linkcheck.strformat import unicode_safe
from linkcheck.url import url_is_absolute

# all the URL classes
import linkcheck.checker.fileurl
import linkcheck.checker.unknownurl
import linkcheck.checker.ftpurl
import linkcheck.checker.gopherurl
import linkcheck.checker.httpurl
import linkcheck.checker.httpsurl
import linkcheck.checker.mailtourl
import linkcheck.checker.telneturl
import linkcheck.checker.nntpurl


def absolute_url (base_url, base_ref, parent_url):
    """
    Search for the absolute url to detect the link type. This does not
    join any url fragments together!

    @param base_url: base url from a link tag
    @type base_url: string or None
    @param base_ref: base url from <base> tag
    @type base_ref: string or None
    @param parent_url: url of parent document
    @type parent_url: string or None
    """
    if base_url and url_is_absolute(base_url):
        return base_url
    elif base_ref and url_is_absolute(base_ref):
        return base_ref
    elif parent_url and url_is_absolute(parent_url):
        return parent_url
    return u""


def get_url_from (base_url, recursion_level, aggregate,
                  parent_url=None, base_ref=None, line=0, column=0,
                  name=u""):
    """
    Get url data from given base data.

    @param base_url: base url from a link tag
    @type base_url: string or None
    @param recursion_level: current recursion level
    @type recursion_level: number
    @param aggregate: aggregate object
    @type aggregate: linkcheck.checker.aggregate.Consumer
    @param parent_url: parent url
    @type parent_url: string or None
    @param base_ref: base url from <base> tag
    @type base_ref string or None
    @param line: line number
    @type line: number
    @param column: column number
    @type column: number
    @param name: link name
    @type name: string
    """
    if base_url is not None:
        base_url = unicode_safe(base_url)
    if parent_url is not None:
        parent_url = unicode_safe(parent_url)
    if base_ref is not None:
        base_ref = unicode_safe(base_ref)
    name = unicode_safe(name)
    url = absolute_url(base_url, base_ref, parent_url).lower()
    klass = get_urlclass_from(url)
    return klass(base_url, recursion_level, aggregate,
                 parent_url=parent_url, base_ref=base_ref,
                 line=line, column=column, name=name)


def get_urlclass_from (url):
    """Return checker class for given URL."""
    if url.startswith("http:"):
        klass = linkcheck.checker.httpurl.HttpUrl
    elif url.startswith("ftp:"):
        klass = linkcheck.checker.ftpurl.FtpUrl
    elif url.startswith("file:"):
        klass = linkcheck.checker.fileurl.FileUrl
    elif url.startswith("telnet:"):
        klass = linkcheck.checker.telneturl.TelnetUrl
    elif url.startswith("mailto:"):
        klass = linkcheck.checker.mailtourl.MailtoUrl
    elif url.startswith("gopher:"):
        klass = linkcheck.checker.gopherurl.GopherUrl
    elif url.startswith("https:"):
        klass = linkcheck.checker.httpsurl.HttpsUrl
    elif url.startswith(("nntp:", "news:", "snews:")):
        klass = linkcheck.checker.nntpurl.NntpUrl
    elif linkcheck.checker.unknownurl.is_unknown_url(url):
        # unknown url
        klass = linkcheck.checker.unknownurl.UnknownUrl
    else:
        # assume local file
        klass = linkcheck.checker.fileurl.FileUrl
    return klass


def get_index_html (urls):
    """
    Construct artificial index.html from given URLs.

    @param urls: list with url strings
    @type urls: list of string
    """
    lines = ["<html>", "<body>"]
    for entry in urls:
        name = cgi.escape(entry)
        url = cgi.escape(urllib.quote(entry))
        lines.append('<a href="%s">%s</a>' % (url, name))
    lines.extend(["</body>", "</html>"])
    return os.linesep.join(lines)



class StoringHandler (logging.Handler):
    """Store all emitted log messages in a size-limited list.
    Used by the CSS syntax checker."""

    def __init__ (self, maxrecords=100):
        logging.Handler.__init__(self)
        self.storage = []
        self.maxrecords = maxrecords

    def emit (self, record):
        if len(self.storage) >= self.maxrecords:
            self.storage.pop()
        self.storage.append(record)
