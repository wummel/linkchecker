# -*- coding: iso-8859-1 -*-
"""Default handler classes"""
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

import sys


class HtmlPrinter (object):
    """handles all functions by printing the function name and attributes"""

    def __init__ (self, fd=sys.stdout):
        """write to given file descriptor"""
        self.fd = fd


    def _print (self, *attrs):
        print >> self.fd, self.mem, attrs


    def _errorfun (self, msg, name):
        """print msg to stderr with name prefix"""
        print >> sys.stderr, name, msg


    def error (self, msg):
        """signal a filter/parser error"""
        self._errorfun(msg, "error:")


    def warning (self, msg):
        """signal a filter/parser warning"""
        self._errorfun(msg, "warning:")


    def fatalError (self, msg):
        """signal a fatal filter/parser error"""
        self._errorfun(msg, "fatal error:")


    def __getattr__ (self, name):
        """remember the func name"""
        self.mem = name
        return self._print


class HtmlPrettyPrinter (object):
    """Print out all parsed HTML data"""

    def __init__ (self, fd=sys.stdout):
        """write to given file descriptor"""
        self.fd = fd


    def comment (self, data):
        """print comment"""
        self.fd.write("<!--%s-->" % data)


    def startElement (self, tag, attrs):
        """print start element"""
        self.fd.write("<%s"%tag.replace("/", ""))
        for key, val in attrs.iteritems():
            if val is None:
                self.fd.write(" %s"%key)
            else:
                self.fd.write(" %s=\"%s\"" % (key, quote_attrval(val)))
        self.fd.write(">")


    def endElement (self, tag):
        """print end element"""
        self.fd.write("</%s>" % tag)


    def doctype (self, data):
        """print document type"""
        self.fd.write("<!DOCTYPE%s>" % data)


    def pi (self, data):
        """print pi"""
        self.fd.write("<?%s?>" % data)


    def cdata (self, data):
        """print cdata"""
        self.fd.write("<![CDATA[%s]]>"%data)


    def characters (self, data):
        """print characters"""
        self.fd.write(data)


def quote_attrval (val):
    """quote a HTML attribute to be able to wrap it in double quotes"""
    return val.replace('"', '&quot;')

