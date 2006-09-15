# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
import socket
import select
import re
import urllib
import nntplib
import ftplib
import linkcheck.httplib2
import linkcheck.strformat
import linkcheck.dns.exception

# helper alias
unicode_safe = linkcheck.strformat.unicode_safe

# Catch these exception on syntax checks.
ExcSyntaxList = [
    linkcheck.LinkCheckerError,
]

# Catch these exceptions on content and connect checks. All other
# exceptions are internal or system errors
ExcCacheList = [
    IOError,
    OSError, # OSError is thrown on Windows when a file is not found
    linkcheck.LinkCheckerError,
    linkcheck.dns.exception.DNSException,
    socket.error,
    select.error,
    # nttp errors (including EOFError)
    nntplib.error_reply,
    nntplib.error_temp,
    nntplib.error_perm,
    nntplib.error_proto,
    EOFError,
    # http error
    linkcheck.httplib2.error,
    # ftp errors
    ftplib.error_reply,
    ftplib.error_temp,
    ftplib.error_perm,
    ftplib.error_proto,
]

# Exceptions that do not put the URL in the cache so that the URL can
# be checked again.
ExcNoCacheList = [
    socket.timeout,
]

ExcList = ExcCacheList + ExcNoCacheList

# registered warnings
Warnings = {
    "url-effective-url":
        _("The effective URL is different from the original."),
    "url-error-getting-content":
        _("Could not get the content of the URL."),
    "url-unicode-domain": _("URL uses a unicode domain."),
    "url-unnormed": _("URL is not normed."),
    "url-anchor-not-found": _("URL anchor was not found."),
    "url-warnregex-found":
        _("The warning regular expression was found in the URL contents."),
    "url-content-too-large": _("The URL content is too large."),
    "file-missing-slash": _("The file: URL is missing a trailing slash."),
    "file-system-path":
        _("The file: path is not the same as the system specific path."),
    "ftp-missing-slash": _("The ftp: URL is missing a trailing slash."),
    "http-robots-denied": _("The http: URL checking has been denied."),
    "http-no-anchor-support": _("The HTTP server had no anchor support."),
    "http-moved-permanent": _("The URL has moved permanently."),
    "http-wrong-redirect":
        _("The URL has been redirected to an URL of a different type."),
    "http-empty-content": _("The URL had no content."),
    "http-cookie-store-error": _("An error occurred while storing a cookie."),
    "http-decompress-error":
        _("An error occurred while decompressing the URL content."),
    "http-unsupported-encoding":
        _("The URL content is encoded with an unknown encoding."),
    "ignored-url": _("The URL has been ignored."),
    "mail-no-addresses": _("The mailto: URL contained no addresses."),
    "mail-no-mx-host": _("The mail MX host could not be found."),
    "mail-unverified-address":
        _("The mailto: address could not be verified."),
    "mail-no-connection":
        _("No connection to a MX host could be established."),
    "nntp-no-server": _("No NNTP server was found."),
    "nntp-no-newsgroup": _("The NNTP newsgroup could not be found."),
    "nntp-busy": _("The NNTP server was busy."),
}

# file extensions we can parse recursively
extensions = {
    "html": re.compile(r'(?i)\.s?html?$'),
    "opera": re.compile(r'^(?i)opera.adr$'), # opera bookmark file
    "css": re.compile(r'(?i)\.css$'), # CSS stylesheet
}


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
    if base_url and linkcheck.url.url_is_absolute(base_url):
        return base_url
    elif base_ref and linkcheck.url.url_is_absolute(base_ref):
        return base_ref
    elif parent_url and linkcheck.url.url_is_absolute(parent_url):
        return parent_url
    return u""


def get_url_from (base_url, recursion_level, aggregate,
                  parent_url=None, base_ref=None, line=0, column=0,
                  name=u"", assume_local=False):
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
    klass = get_urlclass_from(url, assume_local)
    return klass(base_url, recursion_level, aggregate,
                 parent_url=parent_url, base_ref=base_ref,
                 line=line, column=column, name=name)


def get_urlclass_from (url, assume_local):
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
    elif url.startswith("nntp:") or \
         url.startswith("news:") or \
         url.startswith("snews:"):
        klass = linkcheck.checker.nntpurl.NntpUrl
    elif assume_local:
        # assume local file
        klass = linkcheck.checker.fileurl.FileUrl
    else:
        # unknown url
        klass = linkcheck.checker.unknownurl.UnknownUrl
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
