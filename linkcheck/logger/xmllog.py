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

    def start_output (self):
        """print start of checking info as xml comment"""
        linkcheck.logger.Logger.start_output(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        self.fd.write('<?xml version="1.0"?>')
        self.fd.write(os.linesep)
        if self.has_field("intro"):
            self.fd.write("<!--")
            self.fd.write(os.linesep)
            self.fd.write("  "+_("created by %s at %s") %
              (linkcheck.configuration.AppName,
               linkcheck.strformat.strtime(self.starttime)))
            self.fd.write(os.linesep)
            self.fd.write("  "+_("Get the newest version at %s") %
                          linkcheck.configuration.Url)
            self.fd.write(os.linesep)
            self.fd.write("  "+_("Write comments and bugs to %s") %
                          linkcheck.configuration.Email)
            self.fd.write(os.linesep)
            self.fd.write(os.linesep)
            self.fd.write("-->")
            self.fd.write(os.linesep)
            self.fd.write(os.linesep)
        self.fd.write('<GraphXML>\n<graph isDirected="true">')
        self.fd.write(os.linesep)
        self.flush()

    def new_url (self, url_data):
        """write one node and all possible edges"""
        if self.fd is None: return
        node = url_data
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.fd.write('  <node name="%d" ' % node.id)
            self.fd.write(">\n")
            if self.has_field("realurl"):
                self.fd.write("    <label>%s</label>" % \
                              xmlquote(node.url))
                self.fd.write(os.linesep)
            self.fd.write("    <data>")
            self.fd.write(os.linesep)
            if node.dltime >= 0 and self.has_field("dltime"):
                self.fd.write("      <dltime>%f</dltime>" % node.dltime)
                self.fd.write(os.linesep)
            if node.dlsize >= 0 and self.has_field("dlsize"):
                self.fd.write("      <dlsize>%d</dlsize>" % node.dlsize)
                self.fd.write(os.linesep)
            if node.checktime and self.has_field("checktime"):
                self.fd.write("      <checktime>%f</checktime>" \
                              % node.checktime)
                self.fd.write(os.linesep)
            if self.has_field("extern"):
                self.fd.write("      <extern>%d</extern>" % \
                          (node.extern and 1 or 0))
                self.fd.write(os.linesep)
            self.fd.write("    </data>")
            self.fd.write(os.linesep)
            self.fd.write("  </node>")
            self.fd.write(os.linesep)
        self.write_edges()

    def write_edges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
        """
        for node in self.nodes.values():
            if self.nodes.has_key(node.parent_url):
                self.fd.write("  <edge")
                self.fd.write(' source="%d"' % \
                              self.nodes[node.parent_url].id)
                self.fd.write(' target="%d"' % node.id)
                self.fd.write(">")
                self.fd.write(os.linesep)
                if self.has_field("url"):
                    self.fd.write("    <label>%s</label>" % \
                                  xmlquote(node.base_url))
                    self.fd.write(os.linesep)
                self.fd.write("    <data>")
                self.fd.write(os.linesep)
                if self.has_field("result"):
                    self.fd.write("      <valid>%d</valid>" % \
                                  (node.valid and 1 or 0))
                    self.fd.write(os.linesep)
                self.fd.write("    </data>")
                self.fd.write(os.linesep)
                self.fd.write("  </edge>")
                self.fd.write(os.linesep)
        self.flush()

    def end_output (self, linknumber=-1):
        """Finish graph output, and print end of checking info as xml
           comment.
        """
        if self.fd is None:
            return
        self.fd.write("</graph>")
        self.fd.write(os.linesep)
        self.fd.write("</GraphXML>")
        self.fd.write(os.linesep)
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write("<!-- ")
            self.fd.write(_("Stopped checking at %s (%s)") % \
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write(os.linesep)
            self.fd.write("-->")
        self.flush()
        self.fd = None
