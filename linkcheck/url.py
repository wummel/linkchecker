# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Functions for parsing and matching URL strings.
"""

import re
import os
import urlparse
import urllib
import requests
from . import log, LOG_CHECK

for scheme in ('ldap', 'irc'):
    if scheme not in urlparse.uses_netloc:
        urlparse.uses_netloc.append(scheme)

# The character set to encode non-ASCII characters in a URL. See also
# http://tools.ietf.org/html/rfc2396#section-2.1
# Note that the encoding is not really specified, but most browsers
# encode in UTF-8 when no encoding is specified by the HTTP headers,
# else they use the page encoding for followed link. See als
# http://code.google.com/p/browsersec/wiki/Part1#Unicode_in_URLs
url_encoding = "utf-8"


# constants defining url part indexes
SCHEME = 0
HOSTNAME = DOMAIN = 1
PORT = 2
DOCUMENT = 3

default_ports = {
    'http': 80,
    'https': 443,
    'nntps': 563,
    'ftp': 21,
}

# adapted from David Wheelers "Secure Programming for Linux and Unix HOWTO"
# http://www.dwheeler.com/secure-programs/Secure-Programs-HOWTO/\
# filter-html.html#VALIDATING-URIS
_basic = {
    "_path": r"\-\_\.\!\~\*\'\(\),",
    "_hex_safe": r"2-9a-f",
    "_hex_full": r"0-9a-f",
    "_part": r"([a-z0-9][-a-z0-9]{0,61}|[a-z])",
}
_safe_char = r"([a-z0-9%(_path)s\+]|"\
             r"(%%[%(_hex_safe)s][%(_hex_full)s]))" % _basic
_safe_scheme_pattern = r"(https?|ftp)"
_safe_domain_pattern = r"(%(_part)s(\.%(_part)s)*\.?)" % _basic
_safe_host_pattern = _safe_domain_pattern+r"(:(80|8080|8000|443))?" % _basic
_safe_path_pattern = r"((/([a-z0-9%(_path)s]|"\
                     r"(%%[%(_hex_safe)s][%(_hex_full)s]))+)*/?)" % _basic
_safe_fragment_pattern = r"%s*" % _safe_char
_safe_cgi = r"%s+(=(%s|/)+)?" % (_safe_char, _safe_char)
_safe_query_pattern = r"(%s(&%s)*)?" % (_safe_cgi, _safe_cgi)
_safe_param_pattern = r"(%s(;%s)*)?" % (_safe_cgi, _safe_cgi)
safe_url_pattern = r"%s://%s%s(#%s)?" % \
    (_safe_scheme_pattern, _safe_host_pattern,
     _safe_path_pattern, _safe_fragment_pattern)

is_safe_char = re.compile("(?i)^%s$" % _safe_char).match
is_safe_url = re.compile("(?i)^%s$" % safe_url_pattern).match
is_safe_domain = re.compile("(?i)^%s$" % _safe_domain_pattern).match
is_safe_host = re.compile("(?i)^%s$" % _safe_host_pattern).match
is_safe_path = re.compile("(?i)^%s$" % _safe_path_pattern).match
is_safe_parameter = re.compile("(?i)^%s$" % _safe_param_pattern).match
is_safe_query = re.compile("(?i)^%s$" % _safe_query_pattern).match
is_safe_fragment = re.compile("(?i)^%s$" % _safe_fragment_pattern).match


# snatched form urlparse.py
def splitparams (path):
    """Split off parameter part from path.
    Returns tuple (path-without-param, param)
    """
    if '/' in path:
        i = path.find(';', path.rfind('/'))
    else:
        i = path.find(';')
    if i < 0:
        return path, ''
    return path[:i], path[i+1:]


def is_numeric_port (portstr):
    """return: integer port (== True) iff portstr is a valid port number,
           False otherwise
    """
    if portstr.isdigit():
        port = int(portstr)
        # 65536 == 2**16
        if 0 < port < 65536:
            return port
    return False


def safe_host_pattern (host):
    """Return regular expression pattern with given host for URL testing."""
    return "(?i)%s://%s%s(#%s)?" % \
     (_safe_scheme_pattern, host, _safe_path_pattern, _safe_fragment_pattern)


def parse_qsl (qs, keep_blank_values=0, strict_parsing=0):
    """Parse a query given as a string argument.

    @param qs: URL-encoded query string to be parsed
    @type qs: string
    @param keep_blank_values: flag indicating whether blank values in
        URL encoded queries should be treated as blank strings.  A
        true value indicates that blanks should be retained as blank
        strings.  The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.
    @type keep_blank_values: bool
    @param strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.
    @type strict_parsing: bool
    @returns: list of triples (key, value, separator) where key and value
      are the splitted CGI parameter and separator the used separator
      for this CGI parameter which is either a semicolon or an ampersand
    @rtype: list of triples
    """
    pairs = []
    name_value_amp = qs.split('&')
    for name_value in name_value_amp:
        if ';' in name_value:
            pairs.extend([x, ';'] for x in name_value.split(';'))
            pairs[-1][1] = '&'
        else:
            pairs.append([name_value, '&'])
    pairs[-1][1] = ''
    r = []
    for name_value, sep in pairs:
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % name_value)
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
            r.append((name, value, sep))
    return r


def idna_encode (host):
    """Encode hostname as internationalized domain name (IDN) according
    to RFC 3490.
    @raise: UnicodeError if hostname is not properly IDN encoded.
    """
    if host and isinstance(host, unicode):
        try:
            host.encode('ascii')
            return host, False
        except UnicodeError:
            uhost = host.encode('idna').decode('ascii')
            return uhost, uhost != host
    return host, False


def url_fix_host (urlparts):
    """Unquote and fix hostname. Returns is_idn."""
    if not urlparts[1]:
        urlparts[2] = urllib.unquote(urlparts[2])
        return False
    userpass, netloc = urllib.splituser(urlparts[1])
    if userpass:
        userpass = urllib.unquote(userpass)
    netloc, is_idn = idna_encode(urllib.unquote(netloc).lower())
    # a leading backslash in path causes urlsplit() to add the
    # path components up to the first slash to host
    # try to find this case...
    i = netloc.find("\\")
    if i != -1:
        # ...and fix it by prepending the misplaced components to the path
        comps = netloc[i:] # note: still has leading backslash
        if not urlparts[2] or urlparts[2] == '/':
            urlparts[2] = comps
        else:
            urlparts[2] = "%s%s" % (comps, urllib.unquote(urlparts[2]))
        netloc = netloc[:i]
    else:
        # a leading ? in path causes urlsplit() to add the query to the
        # host name
        i = netloc.find("?")
        if i != -1:
            netloc, urlparts[3] = netloc.split('?', 1)
        # path
        urlparts[2] = urllib.unquote(urlparts[2])
    if userpass:
        # append AT for easy concatenation
        userpass += "@"
    else:
        userpass = ""
    if urlparts[0] in default_ports:
        dport = default_ports[urlparts[0]]
        host, port = splitport(netloc, port=dport)
        if host.endswith("."):
            host = host[:-1]
        if port != dport:
            host = "%s:%d" % (host, port)
        netloc = host
    urlparts[1] = userpass+netloc
    return is_idn


def url_fix_common_typos (url):
    """Fix common typos in given URL like forgotten colon."""
    if url.startswith("http//"):
        url = "http://" + url[6:]
    elif url.startswith("https//"):
        url = "https://" + url[7:]
    return url


def url_fix_mailto_urlsplit (urlparts):
    """Split query part of mailto url if found."""
    if "?" in urlparts[2]:
        urlparts[2], urlparts[3] = urlparts[2].split('?', 1)


def url_parse_query (query, encoding=None):
    """Parse and re-join the given CGI query."""
    if isinstance(query, unicode):
        if encoding is None:
            encoding = url_encoding
        query = query.encode(encoding, 'ignore')
    # if ? is in the query, split it off, seen at msdn.microsoft.com
    append = ""
    while '?' in query:
        query, rest = query.rsplit('?', 1)
        append = '?'+url_parse_query(rest)+append
    l = []
    for k, v, sep in parse_qsl(query, True):
        k = url_quote_part(k, '/-:,;')
        if v:
            v = url_quote_part(v, '/-:,;')
            l.append("%s=%s%s" % (k, v, sep))
        elif v is None:
            l.append("%s%s" % (k, sep))
        else:
            # some sites do not work when the equal sign is missing
            l.append("%s=%s" % (k, sep))
    return ''.join(l) + append


def urlunsplit (urlparts):
    """Same as urlparse.urlunsplit but with extra UNC path handling
    for Windows OS."""
    res = urlparse.urlunsplit(urlparts)
    if os.name == 'nt' and urlparts[0] == 'file' and '|' not in urlparts[2]:
        # UNC paths must have 4 slashes: 'file:////server/path'
        # Depending on the path in urlparts[2], urlparse.urlunsplit()
        # left only two or three slashes. This is fixed below
        repl = 'file://' if urlparts[2].startswith('//') else 'file:/'
        res = res.replace('file:', repl)
    return res


def url_norm (url, encoding=None):
    """Normalize the given URL which must be quoted. Supports unicode
    hostnames (IDNA encoding) according to RFC 3490.

    @return: (normed url, idna flag)
    @rtype: tuple of length two
    """
    if isinstance(url, unicode):
        # try to decode the URL to ascii since urllib.unquote()
        # handles non-unicode strings differently
        try:
            url = url.encode('ascii')
        except UnicodeEncodeError:
            pass
        encode_unicode = True
    else:
        encode_unicode = False
    urlparts = list(urlparse.urlsplit(url))
    # scheme
    urlparts[0] = urllib.unquote(urlparts[0]).lower()
    # mailto: urlsplit is broken
    if urlparts[0] == 'mailto':
        url_fix_mailto_urlsplit(urlparts)
    # host (with path or query side effects)
    is_idn = url_fix_host(urlparts)
    # query
    urlparts[3] = url_parse_query(urlparts[3], encoding=encoding)
    if urlparts[0] in urlparse.uses_relative:
        # URL has a hierarchical path we should norm
        if not urlparts[2]:
            # Empty path is allowed if both query and fragment are also empty.
            # Note that in relative links, urlparts[0] might be empty.
            # In this case, do not make any assumptions.
            if urlparts[0] and (urlparts[3] or urlparts[4]):
                urlparts[2] = '/'
        else:
            # fix redundant path parts
            urlparts[2] = collapse_segments(urlparts[2])
    # anchor
    urlparts[4] = urllib.unquote(urlparts[4])
    # quote parts again
    urlparts[0] = url_quote_part(urlparts[0], encoding=encoding) # scheme
    urlparts[1] = url_quote_part(urlparts[1], safechars='@:', encoding=encoding) # host
    urlparts[2] = url_quote_part(urlparts[2], safechars=_nopathquote_chars, encoding=encoding) # path
    urlparts[4] = url_quote_part(urlparts[4], encoding=encoding) # anchor
    res = urlunsplit(urlparts)
    if url.endswith('#') and not urlparts[4]:
        # re-append trailing empty fragment
        res += '#'
    if encode_unicode:
        res = unicode(res)
    return (res, is_idn)


_slashes_ro = re.compile(r"/+")
_thisdir_ro = re.compile(r"^\./")
_samedir_ro = re.compile(r"/\./|/\.$")
_parentdir_ro = re.compile(r"^/(\.\./)+|/(?!\.\./)[^/]+/\.\.(/|$)")
_relparentdir_ro = re.compile(r"^(?!\.\./)[^/]+/\.\.(/|$)")
def collapse_segments (path):
    """Remove all redundant segments from the given URL path.
    Precondition: path is an unquoted url path"""
    # replace backslashes
    # note: this is _against_ the specification (which would require
    # backslashes to be left alone, and finally quoted with '%5C')
    # But replacing has several positive effects:
    # - Prevents path attacks on Windows systems (using \.. parent refs)
    # - Fixes bad URLs where users used backslashes instead of slashes.
    #   This is a far more probable case than users having an intentional
    #   backslash in the path name.
    path = path.replace('\\', '/')
    # shrink multiple slashes to one slash
    path = _slashes_ro.sub("/", path)
    # collapse redundant path segments
    path = _thisdir_ro.sub("", path)
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
    """Quote given URL."""
    if not url_is_absolute(url):
        return document_quote(url)
    urlparts = list(urlparse.urlsplit(url))
    urlparts[0] = url_quote_part(urlparts[0]) # scheme
    urlparts[1] = url_quote_part(urlparts[1], ':') # host
    urlparts[2] = url_quote_part(urlparts[2], '/=,') # path
    urlparts[3] = url_quote_part(urlparts[3], '&=,') # query
    l = []
    for k, v, sep in parse_qsl(urlparts[3], True): # query
        k = url_quote_part(k, '/-:,;')
        if v:
            v = url_quote_part(v, '/-:,;')
            l.append("%s=%s%s" % (k, v, sep))
        else:
            l.append("%s%s" % (k, sep))
    urlparts[3] = ''.join(l)
    urlparts[4] = url_quote_part(urlparts[4]) # anchor
    return urlunsplit(urlparts)


def url_quote_part (s, safechars='/', encoding=None):
    """Wrap urllib.quote() to support unicode strings. A unicode string
    is first converted to UTF-8. After that urllib.quote() is called."""
    if isinstance(s, unicode):
        if encoding is None:
            encoding = url_encoding
        s = s.encode(encoding, 'ignore')
    return urllib.quote(s, safechars)

def document_quote (document):
    """Quote given document."""
    doc, query = urllib.splitquery(document)
    doc = url_quote_part(doc, '/=,')
    if query:
        return "%s?%s" % (doc, query)
    return doc


def match_url (url, domainlist):
    """Return True if host part of url matches an entry in given domain list.
    """
    if not url:
        return False
    return match_host(url_split(url)[1], domainlist)


def match_host (host, domainlist):
    """Return True if host matches an entry in given domain list."""
    if not host:
        return False
    for domain in domainlist:
        if domain.startswith('.'):
            if host.endswith(domain):
                return True
        elif host == domain:
            return True
    return False


_nopathquote_chars = "-;/=,~*+()@!"
if os.name == 'nt':
    _nopathquote_chars += "|"
_safe_url_chars = re.escape(_nopathquote_chars + "_:.&#%?[]!")+"a-zA-Z0-9"
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


def url_split (url):
    """Split url in a tuple (scheme, hostname, port, document) where
    hostname is always lowercased.
    Precondition: url is syntactically correct URI (eg has no whitespace)
    """
    scheme, netloc = urllib.splittype(url)
    host, document = urllib.splithost(netloc)
    port = default_ports.get(scheme, 0)
    if host:
        host = host.lower()
        host, port = splitport(host, port=port)
    return scheme, host, port, document


def url_unsplit (parts):
    """Rejoin URL parts to a string."""
    if parts[2] == default_ports.get(parts[0]):
        return "%s://%s%s" % (parts[0], parts[1], parts[3])
    return "%s://%s:%d%s" % parts


def splitport (host, port=0):
    """Split optional port number from host. If host has no port number,
    the given default port is returned.

    @param host: host name
    @ptype host: string
    @param port: the port number (default 0)
    @ptype port: int

    @return: tuple of (host, port)
    @rtype: tuple of (string, int)
    """
    if ":" in host:
        shost, sport = host.split(":", 1)
        iport = is_numeric_port(sport)
        if iport:
            host, port = shost, iport
        elif not sport:
            # empty port, ie. the host was "hostname:"
            host = shost
        else:
            # For an invalid non-empty port leave the host name as is
            pass
    return host, port


def get_content(url, user=None, password=None, proxy=None, data=None,
                addheaders=None):
    """Get URL content and info.

    @return: (decoded text content of URL, headers) or
             (None, errmsg) on error.
    @rtype: tuple (String, dict) or (None, String)
    """
    from . import configuration
    headers = {
        'User-Agent': configuration.UserAgent,
    }
    if addheaders:
        headers.update(addheaders)
    method = 'GET'
    kwargs = dict(headers=headers)
    if user and password:
        kwargs['auth'] = (user, password)
    if data:
        kwargs['data'] = data
        method = 'POST'
    if proxy:
        kwargs['proxy'] = dict(http=proxy)
    from .configuration import get_share_file
    try:
        kwargs["verify"] = get_share_file('cacert.pem')
    except ValueError:
        pass
    try:
        response = requests.request(method, url, **kwargs)
        return response.text, response.headers
    except (requests.exceptions.RequestException,
            requests.exceptions.BaseHTTPError) as msg:
        log.warn(LOG_CHECK, ("Could not get content of URL %(url)s: %(msg)s.") \
          % {"url": url, "msg": str(msg)})
        return None, str(msg)


def shorten_duplicate_content_url(url):
    """Remove anchor part and trailing index.html from URL."""
    if '#' in url:
        url = url.split('#', 1)[0]
    if url.endswith('index.html'):
        return url[:-10]
    if url.endswith('index.htm'):
        return url[:-9]
    return url


def is_duplicate_content_url(url1, url2):
    """Check if both URLs are allowed to point to the same content."""
    if url1 == url2:
        return True
    if url2 in url1:
        url1 = shorten_duplicate_content_url(url1)
        if not url2.endswith('/') and url1.endswith('/'):
            url2 += '/'
        return url1 == url2
    if url1 in url2:
        url2 = shorten_duplicate_content_url(url2)
        if not url1.endswith('/') and url2.endswith('/'):
            url1 += '/'
        return url1 == url2
    return False
