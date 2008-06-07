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
Base class for graph loggers.
"""
from . import Logger
from .. import strformat
from ..decorators import notimplemented
import time
import re


class GraphLogger (Logger):
    """Provide base method to get node data."""

    def __init__ (self, **args):
        """Initialize graph node list and internal id counter."""
        super(GraphLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def get_node (self, url_data):
        """Return new node data or None if node already exists."""
        if not url_data.url:
            return None
        elif url_data.url in self.nodes:
            return None
        node = {
            "url": url_data.url,
            "parent_url": url_data.parent_url,
            "id": self.nodeid,
            "label": quote(u"%s (#%d)" % (url_data.get_title(), self.nodeid)),
            "extern": 1 if url_data.extern[0] else 0,
            "checktime": url_data.checktime,
            "dlsize": url_data.dlsize,
            "dltime": url_data.dltime,
            "edge": url_data.name,
            "valid": 1 if url_data.valid else 0,
        }
        self.nodes[node["url"]] = node
        self.nodeid += 1
        return node

    def write_edges (self):
        """
        Write all edges we can find in the graph in a brute-force manner.
        """
        for node in self.nodes.values():
            if node["parent_url"] in self.nodes:
                self.write_edge(node)
        self.flush()

    @notimplemented
    def write_edge (self, node):
        """Write edge data for one node and its parent."""
        pass

    @notimplemented
    def end_graph (self):
        """Write end-of-graph marker."""
        pass

    def end_output (self):
        """Write edges and end of checking info as gml comment."""
        self.write_edges()
        self.end_graph()
        if self.has_part("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %(time)s (%(duration)s)") %
                 {"time": strformat.strtime(self.stoptime),
                  "duration": strformat.strduration_long(duration)})
        self.close_fileoutput()


_disallowed = re.compile(r"[^a-zA-Z0-9 '#(){}\-\[\]\.,;:\!\?]+")

def quote (s):
    """Replace disallowed characters in node labels."""
    return _disallowed.sub(" ", s)
