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

import re
import urlparse
import os
import urllib


# adapted from David Wheelers "Secure Programming for Linux and Unix HOWTO"
# http://www.dwheeler.com/secure-programs/Secure-Programs-HOWTO/filter-html.html#VALIDATING-URIS
_basic = {
    "_az09": r"a-z0-9",
    "_path": r"\-\_\.\!\~\*\'\(\),",
    "_hex_safe": r"2-9a-f",
    "_hex_full": r"0-9a-f",
}
_safe_char = r"([%(_az09)s%(_path)s\+]|(%%[%(_hex_safe)s][%(_hex_full)s]))"%_basic
_safe_scheme_pattern = r"(https?|ftp)"
_safe_host_pattern = r"([%(_az09)s][%(_az09)s\-]*(\.[%(_az09)s][%(_az09)s\-]*)*\.?)(:(80|8080|8000))?"%_basic
_safe_path_pattern = r"((/([%(_az09)s%(_path)s]|(%%[%(_hex_safe)s][%(_hex_full)s]))+)*/?)"%_basic
_safe_fragment_pattern = r"%s*"%_safe_char
_safe_cgi = r"%s+(=%s+)?" % (_safe_char, _safe_char)
_safe_query_pattern = r"(%s(&%s)*)?"%(_safe_cgi, _safe_cgi)
safe_url_pattern = r"%s://%s%s(#%s)?" % \
    (_safe_scheme_pattern, _safe_host_pattern,
     _safe_path_pattern, _safe_fragment_pattern)

is_valid_url = re.compile("(?i)^%s$"%safe_url_pattern).match
is_valid_host = re.compile("(?i)^%s$"%_safe_host_pattern).match
is_valid_path = re.compile("(?i)^%s$"%_safe_path_pattern).match
is_valid_query = re.compile("(?i)^%s$"%_safe_query_pattern).match
is_valid_fragment = re.compile("(?i)^%s$"%_safe_fragment_pattern).match

def is_valid_js_url (urlstr):
    """test javascript urls"""
    url = urlparse.urlsplit(urlstr)
    if url[0].lower()!='http':
        return False
    if not is_valid_host(url[1]):
        return False
    if not is_valid_path(url[2]):
        return False
    if not is_valid_query(url[3]):
        return False
    if not is_valid_fragment(url[4]):
        return False
    return True


def safe_host_pattern (host):
    """return regular expression pattern with given host for url testing"""
    return "(?i)%s://%s%s(#%s)?" % \
     (_safe_scheme_pattern, host, _safe_path_pattern, _safe_fragment_pattern)


# XXX better name/implementation for this function
def stripsite (url):
    """remove scheme and host from url. return host, newurl"""
    url = urlparse.urlsplit(url)
    return url[1], urlparse.urlunsplit( (0,0,url[2],url[3],url[4]) )


def parse_qsl(qs, keep_blank_values=0, strict_parsing=0):
    """Parse a query given as a string argument.

    Arguments:

    qs: URL-encoded query string to be parsed

    keep_blank_values: flag indicating whether blank values in
        URL encoded queries should be treated as blank strings.  A
        true value indicates that blanks should be retained as blank
        strings.  The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.

    strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.

    Returns a list, as G-d intended.
    """
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError, "bad query field: %s" % `name_value`
            elif len(nv) == 1:
                nv = (nv[0], "")
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = urllib.unquote(nv[0].replace('+', ' '))
            value = urllib.unquote(nv[1].replace('+', ' '))
            r.append((name, value))
    return r


def url_norm (url):
    """normalize url which must be quoted"""
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = urllib.unquote(urlparts[0]) # scheme
    urlparts[1] = urllib.unquote(urlparts[1]) # host
    # a leading backslash in path causes urlsplit() to add the
    # path components up to the first slash to host
    # try to find this case...
    i = urlparts[1].find("\\")
    if i != -1:
        # ...and fix it by prepending the misplaced components to the path
        comps = urlparts[1][i:] # note: still has leading backslash
        if not urlparts[2] or urlparts[2]=='/':
            urlparts[2] = comps
        else:
            urlparts[2] = "%s%s" % (comps, urllib.unquote(urlparts[2]))
        urlparts[1] = urlparts[1][:i]
    else:
        urlparts[2] = urllib.unquote(urlparts[2]) # path
    l = []
    for k,v in parse_qsl(urlparts[3], True): # query
        k = urllib.quote(k, '/-:,')
        if v:
            v = urllib.quote(v, '/-:,')
            l.append("%s=%s" % (k, v))
        else:
            l.append(k)
    urlparts[3] = '&'.join(l)
    path = urlparts[2].replace('\\', '/').replace('//', '/')
    if not path or path=='/':
        urlparts[2] = '/'
    else:
        # XXX this works only under windows and posix??
        # collapse redundant path segments
        urlparts[2] = os.path.normpath(path).replace('\\', '/')
        if path.endswith('/'):
            urlparts[2] += '/'
    # quote parts again
    urlparts[0] = urllib.quote(urlparts[0]) # scheme
    urlparts[1] = urllib.quote(urlparts[1], ':') # host
    urlparts[2] = urllib.quote(urlparts[2], '/=,') # path
    return urlparse.urlunsplit(urlparts)


def url_quote (url):
    """quote given url"""
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = urllib.quote(urlparts[0]) # scheme
    urlparts[1] = urllib.quote(urlparts[1], ':') # host
    urlparts[2] = urllib.quote(urlparts[2], '/=,') # path
    urlparts[3] = urllib.quote(urlparts[3], '&=,') # query
    l = []
    for k,v in parse_qsl(urlparts[3], True): # query
        k = urllib.quote(k, '/-:,')
        if v:
            v = urllib.quote(v, '/-:,')
            l.append("%s=%s" % (k, v))
        else:
            l.append(k)
    urlparts[3] = '&'.join(l)
    urlparts[4] = urllib.quote(urlparts[4]) # anchor
    return urlparse.urlunsplit(urlparts)


def document_quote (document):
    """quote given document"""
    doc, query = urllib.splitquery(document)
    doc = urllib.quote(doc, '/=,')
    if query:
        return "%s?%s" % (doc, query)
    return doc


def match_url (url, domainlist):
    """return True if host part of url matches an entry in given domain
       list"""
    if not url:
        return False
    return match_host(spliturl(url)[1], domainlist)


def match_host (host, domainlist):
    """return True if host matches an entry in given domain list"""
    if not host:
        return False
    for domain in domainlist:
        if host.endswith(domain):
            return True
    return False


default_ports = {
    'http' : 80,
    'https' : 443,
    'nntps' : 563,
}

def spliturl (url):
    """split url in a tuple (scheme, hostname, port, document) where
    hostname is always lowercased
    precondition: url is syntactically correct URI (eg has no whitespace)"""
    scheme, netloc = urllib.splittype(url)
    host, document = urllib.splithost(netloc)
    port = default_ports.get(scheme, 80)
    if host:
        host = host.lower()
        host, port = urllib.splitnport(host, port)
    return scheme, host, port, document


# constants defining url part indexes
SCHEME = 0
HOSTNAME = DOMAIN = 1
PORT = 2
DOCUMENT = 3
