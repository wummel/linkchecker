# -*- coding: iso-8859-1 -*-
"""A parser for HTML"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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

import sys
try:
    import htmlsax
except ImportError:
    exctype, value = sys.exc_info()[:2]
    print >>sys.stderr, "Could not import the parser module `htmlsax':", value
    print >>sys.stderr, "Please check your installation of LinkChecker."
    sys.exit(1)


class HtmlParser:
    """Use an internal C SAX parser. We do not define any callbacks
    here for compatibility. Currently recognized callbacks are:
    comment(data): <!--data-->
    startElement(tag, attrs): <tag {attr1:value1,attr2:value2,..}>
    endElement(tag): </tag>
    doctype(data): <!DOCTYPE data?>
    pi(name, data=None): <?name data?>
    cdata(data): <![CDATA[data]]>
    characters(data): data

    additionally, there are error and warning callbacks:
    error(msg)
    warning(msg)
    fatalError(msg)
    """
    def __init__ (self):
        """initialize the internal parser"""
        self.parser = htmlsax.parser(self)

    def __getattr__ (self, name):
        """delegate unknown attrs to self.parser"""
        return getattr(self.parser, name)


class HtmlPrinter (HtmlParser):
    """handles all functions by printing the function name and
       attributes"""
    def _print (self, *attrs):
        print self.mem, attrs, self.last_lineno(), self.last_column()

    def _errorfun (self, msg, name):
        """print msg to stderr with name prefix"""
        pos = "%d:%d:" % (self.lineno(), self.column())
        print >> sys.stderr, name, pos, msg

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
        if hasattr(self.parser, name):
            return getattr(self.parser, name)
        self.mem = name
        return self._print


def _test():
    p = HtmlPrinter()
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
    p = HtmlPrinter()
    p.feed("<img bo\\\nrder=0>")
    p.flush()


if __name__ == '__main__':
    #_test()
    _broken()
