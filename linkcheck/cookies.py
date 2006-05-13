# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2006 Bastian Kleineidam
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
import linkcheck.strformat


class CookieError (Exception):
    """
    Thrown for invalid cookie syntax or conflicting/impossible values.
    """
    pass


unquote = Cookie._unquote
quote = Cookie._quote
has_embedded_dot = re.compile(r"[a-zA-Z0-9]\.[a-zA-Z]").search

class HttpCookie (object):
    """
    A cookie consists of one name-value pair with attributes.
    Each attribute consists of a predefined name (see attribute_names)
    and a value (which is optional for some attributes).
    """

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
        self.name = name
        self.value = value
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        self.calculate_expiration()

    def calculate_expiration (self):
        now = time.time()
        # default: does not expire
        self.expire = None
        if "max-age" in self.attributes:
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
            self.expire = cookielib.http2time(self.attributes["expires"])

    def is_expired (self, now=None):
        if self.expire is None:
            # Does not expire.
            return False
        if now is None:
            now = time.time()
        return now > self.expire

    def __repr__ (self):
        attrs = "; ".join("%s=%r"%(k, v) for k, v in self.attributes.items())
        return "<%s %s=%r; %s>" % (self.__class__.__name__,
         self.name, self.value, attrs)

    def is_valid_for (self, scheme, host, port, path):
        """
        Check validity of this cookie against the desired scheme,
        host and path.
        """
        if self.check_expired() and \
           self.check_domain(host) and \
           self.check_port(port) and \
           self.check_path(path) and \
           self.check_secure(scheme):
            return True
        return False

    def check_expired (self):
        return not self.is_expired()

    def check_domain (self, domain):
        if "domain" not in self.attributes:
            return False
        cdomain = self.attributes["domain"]
        if domain == cdomain:
            return True
        if not domain.endswith(cdomain):
            return False
        if "." in domain[:-len(cdomain)]:
            return False
        return True

    def check_port (self, port):
        return True

    def check_path (self, path):
        if "path" not in self.attributes:
            return False
        return path.startswith(self.attributes["path"])

    def check_secure (self, scheme):
        if "secure" in self.attributes:
            return scheme == "https"
        return True

    def client_header_name (self):
        return "Cookie"

    def set_attribute (self, key, value):
        if self.attributes is None:
            raise CookieError("no NAME=VALUE before attributes found")
        key = key.lower()
        if key not in self.attribute_names:
            raise CookieError("invalid attribute %r" % key)
        value = unquote(value)
        if key == "domain":
            value = value.lower()
            if not value.startswith("."):
                raise CookieError("domain has no leading dot: %r" % value)
            if not has_embedded_dot(value):
                raise CookieError("domain has no embedded dot: %r" % value)
        if key == "max-age":
            try:
                num = int(value)
                if num < 0:
                    raise ValueError("Negative Max-Age")
            except (OverflowError, ValueError):
                raise CookieError("invalid Max-Age number: %r" % value)
        if key == "port":
            ports = value.split(",")
            for port in ports:
                try:
                    num = int(port)
                    if not (0 <= num <= 65535):
                        raise ValueError("Invalid port number")
                except (OverflowError, ValueError):
                    raise CookieError("invalid port number: %r" % port)
        self.attributes[key] = value

    def parse (self, text, patt=Cookie._CookiePattern):
        text = linkcheck.strformat.ascii_safe(text)
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
        self.calculate_expiration()

    def set_default_attributes (self, scheme, host, path):
        scheme = linkcheck.strformat.ascii_safe(scheme)
        host = linkcheck.strformat.ascii_safe(host)
        path = linkcheck.strformat.ascii_safe(path)
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
        return quote(value)

    def server_header_value (self):
        parts = ["%s=%s" % (self.name, quote(self.value))]
        parts += ["%s=%s"% (self.attribute_names[k], self.quote(k, v)) \
                  for k, v in self.attributes.iteritems()]
        return "; ".join(parts)

    def client_header_value (self):
        parts = []
        if "version" in self.attributes:
            parts.append("$Version=%s" % quote(self.attributes["version"]))
        parts.append("%s=%s" % (self.name, quote(self.value)))
        parts += ["$%s=%s"% (self.attribute_names[k], self.quote(k, v)) \
                  for k, v in self.attributes.iteritems() if k != "version"]
        return "; ".join(parts)


class NetscapeCookie (HttpCookie):
    """
    Parses RFC 2109 (Netscape) cookies.
    """

    def __init__ (self, text, scheme, host, path):
        self.parse(text)
        self.set_default_attributes(scheme, host, path)

    def server_header_name (self):
        return "Set-Cookie"


class Rfc2965Cookie (HttpCookie):

    def __init__ (self, text, scheme, host, path):
        self.parse(text)
        self.set_default_attributes(scheme, host, path)

    def check_port (self, port):
        if "port" not in self.attributes:
            return True
        cport = self.attributes["port"]
        ports = [int(x) for x in cport.split(",")]
        return port in ports

    def server_header_name (self):
        return "Set-Cookie2"

    def quote (self, key, value):
        if key == "port":
            return quote(value, LegalChars="")
        return quote(value)


# XXX more methods (equality test)

