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
Base class for graph loggers.
"""
from . import _Logger
from ..decorators import notimplemented
import re


class _GraphLogger (_Logger):
    """Provide base method to get node data."""

    def __init__ (self, **kwargs):
        """Initialize graph node list and internal id counter."""
        args = self.get_args(kwargs)
        super(_GraphLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def log_filter_url(self, url_data, do_print):
        """Update accounting data and log all valid URLs regardless the
        do_print flag.
        """
        self.stats.log_url(url_data, do_print)
        # ignore the do_print flag and determine ourselves if we filter the url
        if url_data.valid:
            self.log_url(url_data)

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
            "label": quote(url_data.title if url_data.title else url_data.name),
            "extern": 1 if url_data.extern else 0,
            "checktime": url_data.checktime,
            "size": url_data.size,
            "dltime": url_data.dltime,
            "edge": quote(url_data.name),
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

    def end_output (self, **kwargs):
        """Write edges and end of checking info as gml comment."""
        self.write_edges()
        self.end_graph()
        if self.has_part("outro"):
            self.write_outro()
        self.close_fileoutput()


_disallowed = re.compile(r"[^a-zA-Z0-9 '#(){}\-\[\]\.,;:\!\?]+")

def quote (s):
    """Replace disallowed characters in node or edge labels.
    Also remove whitespace from beginning or end of label."""
    return _disallowed.sub(" ", s).strip()
