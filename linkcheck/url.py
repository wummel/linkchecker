# -*- coding: iso-8859-1 -*-
"""url utils"""
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

__version__ = "$Revision$"[11:-2]
__date__    = "$Date$"[7:-2]

import re, urlparse, os
from urllib import splittype, splithost, splitnport, splitquery, quote, unquote

# adapted from David Wheelers "Secure Programming for Linux and Unix HOWTO"
_az09 = r"a-z0-9"
_path = r"\-\_\.\!\~\*\'\(\)"
_hex_safe = r"2-9a-f"
_hex_full = r"0-9a-f"
_safe_scheme_pattern = r"(https?|ftp)"
_safe_host_pattern = r"([%(_az09)s][%(_az09)s\-]*(\.[%(_az09)s][%(_az09)s\-]*)*\.?)"%locals()
_safe_path_pattern = r"((/([%(_az09)s%(_path)s]|(%%[%(_hex_safe)s][%(_hex_full)s]))+)*/?)"%locals()
_safe_fragment_pattern = r"(\#([%(_az09)s%(_path)s\+]|(%%[%(_hex_safe)s][%(_hex_full)s]))+)?"%locals()
safe_url_pattern = "(?i)"+_safe_scheme_pattern+"://"+_safe_host_pattern+\
                    _safe_path_pattern+_safe_fragment_pattern

is_valid_url = re.compile("^%s$"%safe_url_pattern).match

def safe_host_pattern (host):
    return _safe_scheme_pattern+"://"+host+ \
           _safe_path_pattern+_safe_fragment_pattern


# XXX better name/implementation for this function
def stripsite (url):
    """remove scheme and host from url. return host, newurl"""
    url = urlparse.urlsplit(url)
    return url[1], urlparse.urlunsplit( (0,0,url[2],url[3],url[4]) )


def url_norm (url):
    """unquote and normalize url which must be quoted"""
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = unquote(urlparts[0])
    urlparts[1] = unquote(urlparts[1])
    urlparts[2] = unquote(urlparts[2])
    urlparts[4] = unquote(urlparts[4])
    path = urlparts[2].replace('\\', '/')
    if not path or path=='/':
        urlparts[2] = '/'
    else:
        # XXX this works only under windows and posix??
        # collapse redundant path segments
        urlparts[2] = os.path.normpath(path).replace('\\', '/')
        if path.endswith('/'):
            urlparts[2] += '/'
    return urlparse.urlunsplit(urlparts)


def url_quote (url):
    """quote given url"""
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = quote(urlparts[0])
    urlparts[1] = quote(urlparts[1], ':')
    urlparts[2] = quote(urlparts[2], '/')
    urlparts[4] = quote(urlparts[4])
    return urlparse.urlunsplit(urlparts)


def document_quote (document):
    """quote given document"""
    doc, query = splitquery(document)
    doc = quote(doc, '/')
    if query:
        return "%s?%s" % (doc, query)
    return doc


default_ports = {
    'http' : 80,
    'https' : 443,
    'nntps' : 563,
}

def spliturl (url):
    """split url in a tuple (scheme, hostname, port, document) where
    hostname is always lowercased
    precondition: url is syntactically correct URI (eg has no whitespace)"""
    scheme, netloc = splittype(url)
    host, document = splithost(netloc)
    port = default_ports.get(scheme, 80)
    if host:
        host = host.lower()
        host, port = splitnport(host, port)
    return scheme, host, port, document


# constants defining url part indexes
SCHEME = 0
HOSTNAME = DOMAIN = 1
PORT = 2
DOCUMENT = 3
