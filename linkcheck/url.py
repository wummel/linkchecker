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
import os
import urlparse
import urllib

# constants defining url part indexes
SCHEME = 0
HOSTNAME = DOMAIN = 1
PORT = 2
DOCUMENT = 3

default_ports = {
    'http' : 80,
    'https' : 443,
    'nntps' : 563,
}

# adapted from David Wheelers "Secure Programming for Linux and Unix HOWTO"
# http://www.dwheeler.com/secure-programs/Secure-Programs-HOWTO/\
# filter-html.html#VALIDATING-URIS
_basic = {
    "_az09": r"a-z0-9",
    "_path": r"\-\_\.\!\~\*\'\(\),",
    "_hex_safe": r"2-9a-f",
    "_hex_full": r"0-9a-f",
}
_safe_char = r"([%(_az09)s%(_path)s\+]|"\
             r"(%%[%(_hex_safe)s][%(_hex_full)s]))" % _basic
_safe_scheme_pattern = r"(https?|ftp)"
_safe_domain_pattern = r"([%(_az09)s][%(_az09)s\-]*"\
                       r"(\.[%(_az09)s][%(_az09)s\-]*)*\.?)" % _basic
_safe_host_pattern = _safe_domain_pattern+r"(:(80|8080|8000))?" % _basic
_safe_path_pattern = r"((/([%(_az09)s%(_path)s]|"\
                     r"(%%[%(_hex_safe)s][%(_hex_full)s]))+)*/?)" % _basic
_safe_fragment_pattern = r"%s*" % _safe_char
_safe_cgi = r"%s+(=(%s|/)+)?" % (_safe_char, _safe_char)
_safe_query_pattern = r"(%s(&%s)*)?" % (_safe_cgi, _safe_cgi)
_safe_param_pattern = r"(%s(;%s)*)?" % (_safe_cgi, _safe_cgi)
safe_url_pattern = r"%s://%s%s(#%s)?" % \
    (_safe_scheme_pattern, _safe_host_pattern,
     _safe_path_pattern, _safe_fragment_pattern)

is_safe_url = re.compile("(?i)^%s$" % safe_url_pattern).match
is_safe_domain = re.compile("(?i)^%s$" % _safe_domain_pattern).match
is_safe_host = re.compile("(?i)^%s$" % _safe_host_pattern).match
is_safe_path = re.compile("(?i)^%s$" % _safe_path_pattern).match
is_safe_parameter = re.compile("(?i)^%s$" % _safe_param_pattern).match
is_safe_query = re.compile("(?i)^%s$" % _safe_query_pattern).match
is_safe_fragment = re.compile("(?i)^%s$" % _safe_fragment_pattern).match

# snatched form urlparse.py
def splitparams (path):
    if '/'  in path:
        i = path.find(';', path.rfind('/'))
        if i < 0:
            return path, ''
    else:
        i = path.find(';')
    return path[:i], path[i+1:]


def is_safe_js_url (urlstr):
    """test javascript URLs"""
    url = list(urlparse.urlsplit(urlstr))
    if url[0].lower() != 'http':
        return False
    if not is_safe_host(url[1]):
        return False
    if ";" in urlstr:
        url[2], parameter = splitparams(url[2])
        if not is_safe_parameter(parameter):
            return False
    if not is_safe_path(url[2]):
        return False
    if not is_safe_query(url[3]):
        return False
    if not is_safe_fragment(url[4]):
        return False
    return True


def is_numeric_port (portstr):
    """return True iff portstr is a valid port number"""
    if portstr.isdigit():
        port = int(portstr)
        # 65536 == 2**16
        return 0 < port < 65536
    return False


def safe_host_pattern (host):
    """return regular expression pattern with given host for URL testing"""
    return "(?i)%s://%s%s(#%s)?" % \
     (_safe_scheme_pattern, host, _safe_path_pattern, _safe_fragment_pattern)


# XXX better name/implementation for this function
def stripsite (url):
    """remove scheme and host from URL. return host, newurl"""
    url = urlparse.urlsplit(url)
    return url[1], urlparse.urlunsplit((0, 0, url[2], url[3], url[4]))


def parse_qsl (qs, keep_blank_values=0, strict_parsing=0):
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
                # None value indicates missing equal sign
                nv = (nv[0], None)
            else:
                continue
        if nv[1] or keep_blank_values:
            name = urllib.unquote(nv[0].replace('+', ' '))
            if nv[1]:
                value = urllib.unquote(nv[1].replace('+', ' '))
            else:
                value = nv[1]
            r.append((name, value))
    return r


def idna_encode (host):
    """Encode hostname as internationalized domain name (IDN) according
       to RFC 3490."""
    if host and isinstance(host, unicode):
        uhost = host.encode('idna').decode('ascii')
        return uhost, uhost != host
    return host, False


def url_norm (url):
    """Fix and normalize URL which must be quoted. Supports unicode
       hostnames (IDNA encoding) according to RFC 3490.

       @return (normed url, idna flag)
    """
    urlparts = list(urlparse.urlsplit(url))
    # scheme
    urlparts[0] = urllib.unquote(urlparts[0]).lower()
    # host
    urlparts[1], is_idn = idna_encode(urllib.unquote(urlparts[1]).lower())
    # a leading backslash in path causes urlsplit() to add the
    # path components up to the first slash to host
    # try to find this case...
    i = urlparts[1].find("\\")
    if i != -1:
        # ...and fix it by prepending the misplaced components to the path
        comps = urlparts[1][i:] # note: still has leading backslash
        if not urlparts[2] or urlparts[2] == '/':
            urlparts[2] = comps
        else:
            urlparts[2] = "%s%s" % (comps, urllib.unquote(urlparts[2]))
        urlparts[1] = urlparts[1][:i]
    else:
        urlparts[2] = urllib.unquote(urlparts[2]) # path
    if urlparts[1]:
        userpass, host = urllib.splituser(urlparts[1])
        if userpass:
            # append AT for easy concatenation
            userpass += "@"
        else:
            userpass = ""
        host, port = urllib.splitnport(host)
        # remove trailing dot
        if host.endswith("."):
            host = host[:-1]
        # remove a default (or invalid) port
        if port in [-1, None, default_ports.get(urlparts[0])]:
            urlparts[1] = userpass+host
        else:
            urlparts[1] = "%s%s:%d" % (userpass, host, port)
    l = []
    for k, v in parse_qsl(urlparts[3], True): # query
        k = urllib.quote(k, '/-:,')
        if v:
            v = urllib.quote(v, '/-:,')
            l.append("%s=%s" % (k, v))
        elif v is None:
            l.append(k)
        else:
            # some sites do not work when the equal sign is missing
            l.append("%s=" % k)
    urlparts[3] = '&'.join(l)
    if not urlparts[2]:
        # empty path should be a slash, but not in certain schemes
        # note that in relative links, urlparts[0] might be empty
        # in this case, do not make any assumptions
        if urlparts[0] and urlparts[0] not in urlparse.non_hierarchical:
            urlparts[2] = '/'
    else:
        # fix redundant path parts
        urlparts[2] = collapse_segments(urlparts[2])
    # quote parts again
    urlparts[0] = urllib.quote(urlparts[0]) # scheme
    urlparts[1] = urllib.quote(urlparts[1], '@:') # host
    urlparts[2] = urllib.quote(urlparts[2], _nopathquote_chars) # path
    res = urlparse.urlunsplit(urlparts)
    if url.endswith('#') and not urlparts[4]:
        # re-append trailing empty fragment
        res += '#'
    return (res, is_idn)


_slashes_ro = re.compile(r"/+")
_samedir_ro = re.compile(r"/\./|/\.$")
_parentdir_ro = re.compile(r"^/(\.\./)+|/(?!\.\./)[^/]+/\.\.(/|$)")
_relparentdir_ro = re.compile(r"^(?!\.\./)[^/]+/\.\.(/|$)")
def collapse_segments (path):
    """Remove all redundant segments from the given URL path.
       Precondition: path is an unquoted url path
    """
    # replace backslashes
    # note: this is _against_ the specification (which would require
    # backslashes to be left alone, and finally quoted with '%5C')
    # But replacing has several positive effects:
    # - Prevents path attacks on Windows systems (using \.. parent refs)
    # - Fixes bad urls where users used backslashes instead of slashes.
    #   This is a far more probable case than users having an intentional
    #   backslash in the path name.
    path = path.replace('\\', '/')
    # shrink multiple slashes to one slash
    path = _slashes_ro.sub("/", path)
    # collapse redundant path segments
    path = _samedir_ro.sub("/", path)
    # collapse parent path segments
    # note: here we exploit the fact that the replacements happen
    # to be from left to right (see also _parentdir_ro above)
    newpath = _parentdir_ro.sub("/", path)
    while newpath != path:
        path = newpath
        newpath = _parentdir_ro.sub("/", path)
    # collapse parent path segments of relative paths
    # (ie. without leading slash)
    newpath = _relparentdir_ro.sub("", path)
    while newpath != path:
        path = newpath
        newpath = _relparentdir_ro.sub("", path)
    return path


url_is_absolute = re.compile("^[a-z]+:", re.I).match


def url_quote (url):
    """quote given URL"""
    if not url_is_absolute(url):
        return document_quote(url)
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = urllib.quote(urlparts[0]) # scheme
    urlparts[1] = urllib.quote(urlparts[1], ':') # host
    urlparts[2] = urllib.quote(urlparts[2], '/=,') # path
    urlparts[3] = urllib.quote(urlparts[3], '&=,') # query
    l = []
    for k, v in parse_qsl(urlparts[3], True): # query
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


_nopathquote_chars = r"-;/=,~*+()@"
if os.name == 'nt':
    _nopathquote_chars += "|"
_safe_url_chars = _nopathquote_chars + r"a-zA-Z0-9_:\.&#%\?"
_safe_url_chars_ro = re.compile(r"^[%s]*$" % _safe_url_chars)
def url_needs_quoting (url):
    """Check if url needs percent quoting. Note that the method does
       only check basic character sets, and not any other syntax.
       The URL might still be syntactically incorrect even when
       it is properly quoted.
    """
    if url.rstrip() != url:
        # handle trailing whitespace as a special case
        # since '$' matches immediately before a end-of-line
        return True
    return not _safe_url_chars_ro.match(url)


def spliturl (url):
    """Split url in a tuple (scheme, hostname, port, document) where
       hostname is always lowercased.
       Precondition: url is syntactically correct URI (eg has no whitespace)
    """
    scheme, netloc = urllib.splittype(url)
    host, document = urllib.splithost(netloc)
    port = default_ports.get(scheme, 80)
    if host:
        host = host.lower()
        host, port = urllib.splitnport(host, port)
    return scheme, host, port, document
