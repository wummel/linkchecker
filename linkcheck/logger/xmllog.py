# -*- coding: iso-8859-1 -*-
"""an xml logger"""
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

import os
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
    """quote characters for XML"""
    return xml.sax.saxutils.escape(s)


def xmlquoteattr (s):
    """quote XML attribute, ready for inclusion with double quotes"""
    return xml.sax.saxutils.escape(s, xmlattr_entities)


def xmlunquote (s):
    """unquote characters from XML"""
    return xml.sax.saxutils.unescape(s)


def xmlunquoteattr (s):
    """unquote attributes from XML"""
    return xml.sax.saxutils.unescape(s, xmlattr_entities)


class XMLLogger (linkcheck.logger.Logger):
    """XML output mirroring the GML structure. Easy to parse with any XML
       tool."""

    def __init__ (self, **args):
        """initialize graph node list and internal id counter"""
        super(XMLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def comment (self, s, **args):
        """Print HTML comment."""
        self.write(u"<!-- ")
        self.write(s, **args)
        self.write(u" -->")

    def start_output (self):
        """print start of checking info as xml comment"""
        linkcheck.logger.Logger.start_output(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        self.writeln(u'<?xml version="1.0"?>')
        if self.has_field("intro"):
            self.comment(_("created by %s at %s") %
                         (linkcheck.configuration.AppName,
                          linkcheck.strformat.strtime(self.starttime)))
            self.comment(_("Get the newest version at %s") %
                         linkcheck.configuration.Url)
            self.comment(_("Write comments and bugs to %s") %
                         linkcheck.configuration.Email)
            self.check_date()
            self.writeln()
        self.writeln(u'<GraphXML>')
        self.writeln(u'<graph isDirected="true">')
        self.flush()

    def new_url (self, url_data):
        """write one node and all possible edges"""
        if self.fd is None:
            return
        node = url_data
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.writeln(u'  <node name="%d">' % node.id)
            if self.has_field("realurl"):
                self.writeln(u"    <label>%s</label>" % xmlquote(node.url))
            self.writeln(u"    <data>")
            if node.dltime >= 0 and self.has_field("dltime"):
                self.writeln(u"      <dltime>%f</dltime>" % node.dltime)
            if node.dlsize >= 0 and self.has_field("dlsize"):
                self.writeln(u"      <dlsize>%d</dlsize>" % node.dlsize)
            if node.checktime and self.has_field("checktime"):
                self.writeln(u"      <checktime>%f</checktime>" %
                             node.checktime)
            if self.has_field("extern"):
                self.writeln(u"      <extern>%d</extern>" %
                             (node.extern and 1 or 0))
            self.writeln(u"    </data>")
            self.writeln(u"  </node>")
        self.write_edges()

    def write_edges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
        """
        for node in self.nodes.values():
            if self.nodes.has_key(node.parent_url):
                self.write(u"  <edge")
                self.write(u' source="%d"' % self.nodes[node.parent_url].id)
                self.writeln(u' target="%d">' % node.id)
                if self.has_field("url"):
                    self.writeln(u"    <label>%s</label>" % \
                                 xmlquote(node.base_url))
                self.writeln(u"    <data>")
                if self.has_field("result"):
                    self.writeln(u"      <valid>%d</valid>" % \
                                 (node.valid and 1 or 0))
                self.writeln(u"    </data>")
                self.writeln(u"  </edge>")
        self.flush()

    def end_output (self, linknumber=-1):
        """Finish graph output, and print end of checking info as xml
           comment.
        """
        if self.fd is None:
            return
        self.writeln(u"</graph>")
        self.writeln(u"</GraphXML>")
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %s (%s)") % \
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration(duration)))
        self.flush()
        if self.close_fd:
            self.fd.close()
        self.fd = None
