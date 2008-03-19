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
A GraphXML logger.
"""

import xmllog


class GraphXMLLogger (xmllog.XMLLogger):
    """
    XML output mirroring the GML structure. Easy to parse with any XML
    tool.
    """

    def __init__ (self, **args):
        """
        Initialize graph node list and internal id counter.
        """
        super(GraphXMLLogger, self).__init__(**args)
        self.nodes = {}
        self.nodeid = 0

    def start_output (self):
        """
        Write start of checking info as xml comment.
        """
        super(GraphXMLLogger, self).start_output()
        self.xml_start_output()
        self.xml_starttag(u'GraphXML')
        self.xml_starttag(u'graph', attrs={u"isDirected": u"true"})
        self.flush()

    def log_url (self, url_data):
        """
        Write one node and all possible edges.
        """
        node = url_data
        if node.url and node.url not in self.nodes:
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.xml_starttag(u'node', attrs={u"name": u"%d" % node.id})
            # XXX further
            if self.has_part("realurl"):
                self.xml_tag(u"label", node.url)
            self.xml_starttag(u"data")
            if node.dltime >= 0 and self.has_part("dltime"):
                self.xml_tag(u"dltime", u"%f" % node.dltime)
            if node.dlsize >= 0 and self.has_part("dlsize"):
                self.xml_tag(u"dlsize", u"%d" % node.dlsize)
            if node.checktime and self.has_part("checktime"):
                self.xml_tag(u"checktime", u"%f" % node.checktime)
            if self.has_part("extern"):
                self.xml_tag(u"extern", u"%d" % (node.extern[0] and 1 or 0))
            self.xml_endtag(u"data")
            self.xml_endtag(u"node")
        self.write_edges()

    def write_edges (self):
        """
        Write all edges we can find in the graph in a brute-force
        manner. Better would be a mapping of parent URLs.
        """
        for node in self.nodes.itervalues():
            if node.parent_url in self.nodes:
                attrs = {
                    u"source": u"%d" % self.nodes[node.parent_url].id,
                    u"target": u"%d" % node.id,
                }
                self.xml_starttag(u"edge", attrs=attrs)
                if self.has_part("url"):
                    self.xml_tag(u"label", node.base_url or u"")
                self.xml_starttag(u"data")
                if self.has_part("result"):
                    self.xml_tag(u"valid", u"%d" % (node.valid and 1 or 0))
                self.xml_endtag(u"data")
                self.xml_endtag(u"edge")
        self.flush()

    def end_output (self):
        """
        Finish graph output, and print end of checking info as xml comment.
        """
        self.xml_endtag(u"graph")
        self.xml_endtag(u"GraphXML")
        self.xml_end_output()
        self.close_fileoutput()
