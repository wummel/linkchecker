# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2006 Bastian Kleineidam
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
Base class for XML loggers.
"""

import time
import xml.sax.saxutils

import linkcheck.logger
import linkcheck.configuration


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


def xmlunquote (s):
    """
    Unquote characters from XML.
    """
    return xml.sax.saxutils.unescape(s)


def xmlunquoteattr (s):
    """
    Unquote attributes from XML.
    """
    return xml.sax.saxutils.unescape(s, xmlattr_entities)


class XMLLogger (linkcheck.logger.Logger):
    """
    XML output mirroring the GML structure. Easy to parse with any XML
    tool.
    """

    def __init__ (self, **args):
        """
        Initialize graph node list and internal id counter.
        """
        super(XMLLogger, self).__init__(**args)
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

    def xml_start_output (self, version="1.0", encoding="utf8"):
        """
        Write start of checking info as xml comment.
        """
        self.output_encoding = encoding
        self.starttime = time.time()
        self.writeln(u'<?xml version="%s" encoding="%s"?>' %
                     (xmlquoteattr(version), xmlquoteattr(encoding)))
        if self.has_part("intro"):
            self.comment(_("created by %s at %s") %
                         (linkcheck.configuration.AppName,
                          linkcheck.strformat.strtime(self.starttime)))
            self.comment(_("Get the newest version at %s") %
                         linkcheck.configuration.Url)
            self.comment(_("Write comments and bugs to %s") %
                         linkcheck.configuration.Email)
            self.check_date()
            self.writeln()

    def xml_end_output (self):
        """
        Write end of checking info as xml comment.
        """
        if self.has_part("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %s (%s)") %
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration_long(duration)))

    def xml_starttag (self, name, attrs=None):
        """
        Write XML start tag.
        """
        self.write(self.indent*self.level)
        self.write(u"<%s" % xmlquote(name))
        if attrs:
            for name, value in attrs.iteritems():
                args = (xmlquote(name), xmlquoteattr(value))
                self.write(u' %s="%s"' % args)
        self.writeln(u">");
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
            for aname, avalue in attrs.iteritems():
                args = (xmlquote(aname), xmlquoteattr(avalue))
                self.write(u' %s="%s"' % args)
        self.writeln(u">%s</%s>" % (xmlquote(content), xmlquote(name)))
