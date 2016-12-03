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
Default HTML parser handler classes.
"""

import sys
from builtins import bytes

class HtmlPrinter (object):
    """
    Handles all functions by printing the function name and attributes.
    """

    def __init__ (self, fd=sys.stdout):
        """
        Write to given file descriptor.

        @param fd: file like object (default=sys.stdout)
        @type fd: file
        """
        self.fd = fd

    def _print (self, *attrs):
        """
        Print function attributes to stored file descriptor.

        @param attrs: list of values to print
        @type attrs: tuple
        @return: None
        """
        print >> self.fd, self.mem, attrs

    def __getattr__ (self, name):
        """
        Remember the called method name in self.mem.

        @param name: attribute name
        @type name: string
        @return: method which just prints out its arguments
        @rtype: a bound function object
        """
        self.mem = name
        return self._print


class HtmlPrettyPrinter (object):
    """
    Print out all parsed HTML data in encoded form.
    Also stores error and warnings messages.
    """

    def __init__ (self, fd=sys.stdout, encoding="iso8859-1"):
        """
        Write to given file descriptor in given encoding.

        @param fd: file like object (default=sys.stdout)
        @type fd: file
        @param encoding: encoding (default=iso8859-1)
        @type encoding: string
        """
        self.fd = fd
        self.encoding = encoding

    def comment (self, data):
        """
        Print HTML comment.

        @param data: the comment
        @type data: string
        @return: None
        """
        data = data.encode(self.encoding, "ignore")
        self.fd.write(b"<!--%s-->" % data)

    def start_element (self, tag, attrs):
        """
        Print HTML start element.

        @param tag: tag name
        @type tag: string
        @param attrs: tag attributes
        @type attrs: dict
        @return: None
        """
        self._start_element(tag, attrs, ">")

    def start_end_element (self, tag, attrs):
        """
        Print HTML start-end element.

        @param tag: tag name
        @type tag: string
        @param attrs: tag attributes
        @type attrs: dict
        @return: None
        """
        self._start_element(tag, attrs, "/>")

    def _start_element (self, tag, attrs, end):
        """
        Print HTML element with end string.

        @param tag: tag name
        @type tag: string
        @param attrs: tag attributes
        @type attrs: dict
        @param end: either > or />
        @type end: string
        @return: None
        """
        tag = tag.encode(self.encoding, "ignore")
        self.fd.write(b"<%s" % tag.replace(b"/", b""))
        for key, val in attrs.items():
            key = key.encode(self.encoding, "ignore")
            if val is None:
                self.fd.write(b" %s" % key)
            else:
                val = val.encode(self.encoding, "ignore")
                self.fd.write(b' %s="%s"' % (key, quote_attrval(val)))
        self.fd.write(end.encode("utf8"))

    def end_element (self, tag):
        """
        Print HTML end element.

        @param tag: tag name
        @type tag: string
        @return: None
        """
        tag = tag.encode(self.encoding, "ignore")
        self.fd.write(b"</%s>" % tag)

    def doctype (self, data):
        """
        Print HTML document type.

        @param data: the document type
        @type data: string
        @return: None
        """
        data = data.encode(self.encoding, "ignore")
        self.fd.write(b"<!DOCTYPE%s>" % data)

    def pi (self, data):
        """
        Print HTML pi.

        @param data: the tag data
        @type data: string
        @return: None
        """
        data = data.encode(self.encoding, "ignore")
        self.fd.write(b"<?%s?>" % data)

    def cdata (self, data):
        """
        Print HTML cdata.

        @param data: the character data
        @type data: string
        @return: None
        """
        data = data.encode(self.encoding, "ignore")
        self.fd.write(b"<![CDATA[%s]]>" % data)

    def characters (self, data):
        """
        Print characters.

        @param data: the character data
        @type data: string
        @return: None
        """
        data = data.encode(self.encoding, "ignore")
        self.fd.write(data)


def quote_attrval (s):
    """
    Quote a HTML attribute to be able to wrap it in double quotes.

    @param s: the attribute string to quote
    @type s: string
    @return: the quoted HTML attribute
    @rtype: string
    """
    res = []
    for c in bytearray(s):
        if c <= 127:
            # ASCII
            if bytes([c]) == b'&':
                res.append(b"&amp;")
            elif bytes([c]) == b'"':
                res.append(b"&quot;")
            else:
                res.append(bytes([c]))
        else:
            res.append(b"&#%d;" % c)
    return b"".join(res)
