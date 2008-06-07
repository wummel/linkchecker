# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
from . import Logger
from .. import configuration, strformat


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


class XMLLogger (Logger):
    """XML output; easy to parse with any XML tool."""

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

    def xml_start_output (self, version="1.0", encoding="utf-8"):
        """
        Write start of checking info as xml comment.
        """
        self.output_encoding = encoding
        self.starttime = time.time()
        self.writeln(u'<?xml version="%s" encoding="%s"?>' %
                     (xmlquoteattr(version), xmlquoteattr(encoding)))
        if self.has_part("intro"):
            self.comment(_("created by %(app)s at %(time)s") %
                        {"app": configuration.AppName,
                         "time": strformat.strtime(self.starttime)})
            self.comment(_("Get the newest version at %(url)s") %
                         {'url': configuration.Url})
            self.comment(_("Write comments and bugs to %(email)s") %
                         {'email': configuration.Email})
            self.check_date()
            self.writeln()

    def xml_end_output (self):
        """
        Write end of checking info as xml comment.
        """
        if self.has_part("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %(time)s (%(duration)s)") %
                 {"time": strformat.strtime(self.stoptime),
                  "duration": strformat.strduration_long(duration)})

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
            for aname, avalue in attrs.items():
                args = (xmlquote(aname), xmlquoteattr(avalue))
                self.write(u' %s="%s"' % args)
        self.writeln(u">%s</%s>" % (xmlquote(content), xmlquote(name)))
