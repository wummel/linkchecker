# -*- coding: iso-8859-1 -*-
"""A parser for HTML"""
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
try:
    import htmlsax
except ImportError, msg:
    exctype, value = sys.exc_info()[:2]
    print >>sys.stderr, "Could not import the parser module `htmlsax':", value
    print >>sys.stderr, "Please check your installation of LinkChecker."
    sys.exit(1)


class HtmlPrinter (object):
    """handles all functions by printing the function name and attributes"""
    def _print (self, *attrs):
        print self.mem, attrs


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


def quote_attrval (val):
    """quote a HTML attribute to be able to wrap it in double quotes"""
    return val.replace('"', '&quot;')


def _test():
    p = htmlsax.parser(HtmlPrinter())
    p.feed("<hTml>")
    p.feed("<a href>")
    p.feed("<a href=''>")
    p.feed('<a href="">')
    p.feed("<a href='a'>")
    p.feed('<a href="a">')
    p.feed("<a href=a>")
    p.feed("<a href='\"'>")
    p.feed("<a href=\"'\">")
    p.feed("<a href=' '>")
    p.feed("<a href=a href=b>")
    p.feed("<a/>")
    p.feed("<a href/>")
    p.feed("<a href=a />")
    p.feed("</a>")
    p.feed("<?bla foo?>")
    p.feed("<?bla?>")
    p.feed("<!-- - comment -->")
    p.feed("<!---->")
    p.feed("<!DOCTYPE \"vla foo>")
    p.flush()

def _broken ():
    p = htmlsax.parser(HtmlPrinter())
    # turn on debugging
    p.debug(1)
    p.feed("""<base href="http://www.msnbc.com/news/">""")
    p.flush()


if __name__ == '__main__':
    #_test()
    _broken()
