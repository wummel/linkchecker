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
Base class for XML loggers.
"""

import xml.sax.saxutils
from . import _Logger


xmlattr_entities = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
}


def xmlquote (s):
    """
    Quote characters for XML.
    """
    return xml.sax.saxutils.escape(s)


def xmlquoteattr (s):
    """
    Quote XML attribute, ready for inclusion with double quotes.
    """
    return xml.sax.saxutils.escape(s, xmlattr_entities)


class _XMLLogger (_Logger):
    """Base class for XML output; easy to parse with any XML tool."""

    def __init__ (self, **kwargs):
        """ Initialize graph node list and internal id counter. """
        args = self.get_args(kwargs)
        super(_XMLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.indent = u"  "
        self.level = 0

    def comment (self, s, **args):
        """
        Write XML comment.
        """
        self.write(u"<!-- ")
        self.write(s, **args)
        self.writeln(u" -->")

    def xml_start_output (self):
        """
        Write start of checking info as xml comment.
        """
        self.writeln(u'<?xml version="1.0" encoding="%s"?>' %
             xmlquoteattr(self.get_charset_encoding()))
        if self.has_part("intro"):
            self.write_intro()
            self.writeln()

    def xml_end_output (self):
        """
        Write end of checking info as xml comment.
        """
        if self.has_part("outro"):
            self.write_outro()

    def xml_starttag (self, name, attrs=None):
        """
        Write XML start tag.
        """
        self.write(self.indent*self.level)
        self.write(u"<%s" % xmlquote(name))
        if attrs:
            for name, value in attrs.items():
                args = (xmlquote(name), xmlquoteattr(value))
                self.write(u' %s="%s"' % args)
        self.writeln(u">")
        self.level += 1

    def xml_endtag (self, name):
        """
        Write XML end tag.
        """
        self.level -= 1
        assert self.level >= 0
        self.write(self.indent*self.level)
        self.writeln(u"</%s>" % xmlquote(name))

    def xml_tag (self, name, content, attrs=None):
        """
        Write XML tag with content.
        """
        self.write(self.indent*self.level)
        self.write(u"<%s" % xmlquote(name))
        if attrs:
            for aname, avalue in attrs.items():
                args = (xmlquote(aname), xmlquoteattr(avalue))
                self.write(u' %s="%s"' % args)
        self.writeln(u">%s</%s>" % (xmlquote(content), xmlquote(name)))
