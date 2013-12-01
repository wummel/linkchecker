# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2012 Bastian Kleineidam
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
Parsing and storing of cookies. See [1]RFC 2965 and [2]RFC 2109.
The reason for this module is that neither the cookielib nor the Cookie
modules included in the Python standard library provide a usable interface
for programmable cookie handling.
This module provides parsing of cookies for all formats specified by
the above RFCs, plus smart methods handling data conversion and formatting.
And a cookie storage class is provided.

[1] http://www.faqs.org/rfcs/rfc2965.html
[2] http://www.faqs.org/rfcs/rfc2109.html
"""

import time
import re
import Cookie
import cookielib
import httplib
from cStringIO import StringIO
from . import strformat


class CookieError (StandardError):
    """Thrown for invalid cookie syntax or conflicting/impossible values."""
    pass


unquote = Cookie._unquote
quote = Cookie._quote
has_embedded_dot = re.compile(r"[a-zA-Z0-9]\.[a-zA-Z]").search


# Pattern for finding cookie snatched from Pythons Cookie.py
# Modification: allow whitespace in values.
LegalChars = r"\w\d!#%&'~_`><@,:/\"\$\*\+\-\.\^\|\)\(\?\}\{\="
CookiePattern = re.compile(r"""
    (?P<key>                   # Start of group 'key'
    [%(legalchars)s]+?         # Any word of at least one letter, nongreedy
    )                          # End of group 'key'
    \s*=\s*                    # Equal Sign
    (?P<val>                   # Start of group 'val'
    "(?:[^\\"]|\\.)*"          # Any doublequoted string
    |                          # or
    [%(legalchars)s\s]*        # Any word or empty string
    )                          # End of group 'val'
    \s*;?                      # Probably ending in a semi-colon
    """ % {"legalchars": LegalChars}, re.VERBOSE)


class HttpCookie (object):
    """A cookie consists of one name-value pair with attributes.
    Each attribute consists of a predefined name (see attribute_names)
    and a value (which is optional for some attributes)."""

    # A mapping from the lowercase variant on the left to the
    # appropriate traditional formatting on the right.
    attribute_names = {
        # Old Netscape attribute
        "expires":    "expires",
        # Defined by RFC 2109
        "path":       "Path",
        "comment":    "Comment",
        "domain":     "Domain",
        "max-age":    "Max-Age",
        "secure":     "secure",
        "version":    "Version",
        # Additional attributes defined by RFC 2965
        "commenturl": "CommentURL",
        "discard":    "Discard",
        "port":       "Port",
    }

    def __init__ (self, name, value, attributes=None):
        """Store name, value and attributes. Also calculates expiration
        if given in attributes."""
        self.name = name
        self.value = value
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        self.calculate_expiration()

    def calculate_expiration (self):
        """If "max-age" or "expires" attributes are given, calculate
        the time when this cookie expires.
        Stores the time value in self.expires, or None if this cookie
        does not expire.
        """
        # default: do not expire
        self.expire = None
        if "max-age" in self.attributes:
            now = time.time()
            try:
                maxage = int(self.attributes["max-age"])
                if maxage == 0:
                    # Expire immediately: subtract 1 to be sure since
                    # some clocks have only full second precision.
                    self.expire = now - 1
                else:
                    self.expire = now + maxage
            except (ValueError, OverflowError):
                # note: even self.now + maxage can overflow
                pass
        elif "expires" in self.attributes:
            expiration_date = self.attributes["expires"]
            try:
                self.expire = cookielib.http2time(expiration_date)
            except ValueError:
                # see http://bugs.python.org/issue16181
                raise CookieError("Invalid expiration date in %r" % expiration_date)

    def is_expired (self, now=None):
        """Return True if this cookie is expired, else False."""
        if self.expire is None:
            # Does not expire.
            return False
        if now is None:
            now = time.time()
        return now > self.expire

    def __repr__ (self):
        """Return cookie name, value and attributes as string."""
        attrs = "; ".join("%s=%r"%(k, v) for k, v in self.attributes.items())
        return "<%s %s=%r; %s>" % (self.__class__.__name__,
         self.name, self.value, attrs)

    def is_valid_for (self, scheme, host, port, path):
        """Check validity of this cookie against the desired scheme,
        host and path."""
        if self.check_expired() and \
           self.check_domain(host) and \
           self.check_port(port) and \
           self.check_path(path) and \
           self.check_secure(scheme):
            return True
        return False

    def check_expired (self):
        """Return False if cookie is expired, else True."""
        return not self.is_expired()

    def check_domain (self, domain):
        """Return True if given domain matches this cookie, else False."""
        if "domain" not in self.attributes:
            return False
        cdomain = self.attributes["domain"]
        if domain == cdomain:
            # equality matches
            return True
        if "." not in domain and domain == cdomain[1:]:
            # "localhost" and ".localhost" match
            return True
        if not domain.endswith(cdomain):
            # any suffix matches
            return False
        if "." in domain[:-(len(cdomain)+1)]:
            # prefix must be dot-free
            return False
        return True

    def check_port (self, port):
        """Return True if given port matches this cookie, else False.
        For now, this returns always True."""
        return True

    def check_path (self, path):
        """Return True if given path matches this cookie, else False."""
        if "path" not in self.attributes:
            return False
        return path.startswith(self.attributes["path"])

    def check_secure (self, scheme):
        """Return True if given Scheme is allowed for this cookie, else
        False."""
        if "secure" in self.attributes:
            return scheme == "https"
        return True

    def set_attribute (self, key, value):
        """Helper method to set attribute values. Called when parsing
        cookie data.
        The attribute key and value are checked, and CookieError is
        raised in these cases."""
        if self.attributes is None:
            raise CookieError("no NAME=VALUE before attributes found")
        key = key.lower()
        if key not in self.attribute_names:
            raise CookieError("invalid attribute %r" % key)
        value = unquote(value)
        if key == "domain":
            value = value.lower()
            if not value.startswith(".") and not has_embedded_dot(value):
                if "." in value:
                    raise CookieError("invalid dot in domain %r" % value)
                # supply a leading dot
                value = "."+value
        if key == "max-age":
            try:
                if int(value) < 0:
                    raise ValueError("Negative Max-Age")
            except (OverflowError, ValueError):
                raise CookieError("invalid Max-Age number: %r" % value)
        if key == "port":
            ports = value.split(",")
            for port in ports:
                try:
                    if not (0 <= int(port) <= 65535):
                        raise ValueError("Invalid port number")
                except (OverflowError, ValueError):
                    raise CookieError("invalid port number: %r" % port)
        self.attributes[key] = value

    def parse (self, text, patt=CookiePattern):
        """Parse cookie data."""
        text = strformat.ascii_safe(text.rstrip('\r\n'))
        # reset values
        self.name = None
        self.value = None
        self.attributes = None
        # Our starting point
        i = 0
        # Length of string
        n = len(text)

        while 0 <= i < n:
            # Start looking for a key-value pair.
            match = patt.search(text, i)
            if not match:
                # No more key-value pairs.
                break
            key, value = match.group("key"), match.group("val")
            i = match.end()
            # Parse the key, value in case it's metainfo.
            if self.name is None:
                # Set name and value.
                self.name = key
                self.value = unquote(value)
                self.attributes = {}
            else:
                if key.startswith("$"):
                    key = key[1:]
                self.set_attribute(key, value)
        if self.name is None:
            raise CookieError("missing cookie name in %r" % text)
        self.calculate_expiration()

    def set_default_attributes (self, scheme, host, path):
        """Set domain and path attributes for given scheme, host and
        path."""
        scheme = strformat.ascii_safe(scheme)
        host = strformat.ascii_safe(host)
        path = strformat.ascii_safe(path)
        if "domain" not in self.attributes:
            self.attributes["domain"] = host.lower()
        if "path" not in self.attributes:
            i = path.rfind("/")
            if i == -1:
                path = "/"
            else:
                path = path[:i]
                if not path:
                    path = "/"
            self.attributes["path"] = path
        if not self.check_domain(host):
            cdomain = self.attributes["domain"]
            raise CookieError("domain %r not for cookie %r" % (cdomain, host))
        if not self.check_path(path):
            cpath = self.attributes["path"]
            raise CookieError("domain %r not for cookie %r" % (cpath, path))
        if not self.check_secure(scheme):
            raise CookieError("no secure scheme %r" % scheme)

    def quote (self, key, value):
        """Quote value for given key."""
        return quote(value)

    def server_header_value (self):
        """Return HTTP header value to send to server."""
        parts = ["%s=%s" % (self.name, quote(self.value))]
        parts.extend(["%s=%s"% (self.attribute_names[k], self.quote(k, v)) \
                  for k, v in self.attributes.items()])
        return "; ".join(parts)

    def client_header_value (self):
        """Return HTTP header value to send to client."""
        parts = []
        if "version" in self.attributes:
            parts.append("$Version=%s" % quote(self.attributes["version"]))
        parts.append("%s=%s" % (self.name, self.value))
        parts.extend(["$%s=%s"% (self.attribute_names[k], self.quote(k, v)) \
                  for k, v in self.attributes.items() if k != "version"])
        return "; ".join(parts)

class NetscapeCookie (HttpCookie):
    """Parses RFC 2109 (Netscape) cookies."""

    def __init__ (self, text, scheme, host, path):
        """Parse given cookie data."""
        self.parse(text)
        self.set_default_attributes(scheme, host, path)

    def server_header_name (self):
        """Return "Set-Cookie" as server header name."""
        return "Set-Cookie"

    def __eq__ (self, other):
        """Compare equality of cookie."""
        return (isinstance(other, NetscapeCookie) and
            self.name.lower() == other.name.lower() and
            self.attributes['domain'] == other.attributes['domain'] and
            self.attributes['path'] == other.attributes['path'])

    def __hash__ (self):
        """Cookie hash value"""
        data = (
          self.name.lower(),
          self.attributes['domain'],
          self.attributes['path'],
        )
        return hash(data)



class Rfc2965Cookie (HttpCookie):
    """Parses RFC 2965 cookies."""

    def __init__ (self, text, scheme, host, path):
        """Parse given cookie data."""
        self.parse(text)
        self.set_default_attributes(scheme, host, path)

    def check_port (self, port):
        """Return True if given port matches this cookie, else False."""
        if "port" not in self.attributes:
            return True
        cport = self.attributes["port"]
        return port in [int(x) for x in cport.split(",")]

    def server_header_name (self):
        """Return "Set-Cookie2" as server header name."""
        return "Set-Cookie2"

    def quote (self, key, value):
        """Quote value for given key."""
        if key == "port":
            return quote(value, LegalChars="")
        return quote(value)

    def __eq__ (self, other):
        """Compare equality of cookie."""
        return (isinstance(other, Rfc2965Cookie) and
            self.name.lower() == other.name.lower() and
            self.attributes['domain'].lower() ==
                other.attributes['domain'].lower() and
            self.attributes['path'] == other.attributes['path'])

    def __hash__ (self):
        """Cookie hash value"""
        data = (
          self.name.lower(),
          self.attributes['domain'].lower(),
          self.attributes['path'],
        )
        return hash(data)


def from_file (filename):
    """Parse cookie data from a text file in HTTP header format.

    @return: list of tuples (headers, scheme, host, path)
    """
    entries = []
    with open(filename) as fd:
        lines = []
        for line in fd.readlines():
            line = line.rstrip()
            if not line:
                if lines:
                    entries.append(from_headers("\r\n".join(lines)))
                lines = []
            else:
                lines.append(line)
        if lines:
            entries.append(from_headers("\r\n".join(lines)))
        return entries


def from_headers (strheader):
    """Parse cookie data from a string in HTTP header (RFC 2616) format.

    @return: tuple (headers, scheme, host, path)
    @raises: ValueError for incomplete or invalid data
    """
    fp = StringIO(strheader)
    headers = httplib.HTTPMessage(fp, seekable=True)
    if "Host" not in headers:
        raise ValueError("Required header 'Host:' missing")
    host = headers["Host"]
    scheme = headers.get("Scheme", "http")
    path= headers.get("Path", "/")
    return (headers, scheme, host, path)


## Taken and adpated from the _mechanize package included in Twill.

def cookie_str(cookie):
    """Return string representation of Cookie."""
    h = [(cookie.name, unquote(cookie.value)),
         ("path", cookie.path),
         ("domain", cookie.domain)]
    if cookie.port is not None: h.append(("port", cookie.port))
    #if cookie.path_specified: h.append(("path_spec", None))
    #if cookie.port_specified: h.append(("port_spec", None))
    #if cookie.domain_initial_dot: h.append(("domain_dot", None))
    if cookie.secure: h.append(("secure", None))
    if cookie.expires: h.append(("expires",
                               time2isoz(float(cookie.expires))))
    if cookie.discard: h.append(("discard", None))
    if cookie.comment: h.append(("comment", cookie.comment))
    if cookie.comment_url: h.append(("commenturl", cookie.comment_url))
    #if cookie.rfc2109: h.append(("rfc2109", None))

    keys = cookie.nonstandard_attr_keys()
    keys.sort()
    for k in keys:
        h.append((k, str(cookie.get_nonstandard_attr(k))))

    h.append(("version", str(cookie.version)))

    return join_header_words([h])


def time2isoz(t=None):
    """Return a string representing time in seconds since epoch, t.

    If the function is called without an argument, it will use the current
    time.

    The format of the returned string is like "YYYY-MM-DD hh:mm:ssZ",
    representing Universal Time (UTC, aka GMT).  An example of this format is:

    1994-11-24 08:49:37Z

    """
    if t is None: t = time.time()
    year, mon, mday, hour, min, sec = time.gmtime(t)[:6]
    return "%04d-%02d-%02d %02d:%02d:%02dZ" % (
        year, mon, mday, hour, min, sec)


join_escape_re = re.compile(r"([\"\\])")
def join_header_words(lists):
    """Do the inverse of the conversion done by split_header_words.

    Takes a list of lists of (key, value) pairs and produces a single header
    value.  Attribute values are quoted if needed.

    >>> join_header_words([[("text/plain", None), ("charset", "iso-8859/1")]])
    'text/plain; charset="iso-8859/1"'
    >>> join_header_words([[("text/plain", None)], [("charset", "iso-8859/1")]])
    'text/plain, charset="iso-8859/1"'

    """
    headers = []
    for pairs in lists:
        attr = []
        for k, v in pairs:
            if v is not None:
                if not re.search(r"^\w+$", v):
                    v = join_escape_re.sub(r"\\\1", v)  # escape " and \
                    v = '"%s"' % v
                if k is None:  # Netscape cookies may have no name
                    k = v
                else:
                    k = "%s=%s" % (k, v)
            attr.append(k)
        if attr: headers.append("; ".join(attr))
    return ", ".join(headers)
