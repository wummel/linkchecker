# -*- coding: iso-8859-1 -*-
"""a gml logger"""
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

import time
import os

import linkcheck.logger.standard
import linkcheck.configuration

from linkcheck.i18n import _


class GMLLogger (linkcheck.logger.standard.StandardLogger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """

    def __init__ (self, **args):
        """initialize graph node list and internal id counter"""
        super(GMLLogger, self).__init__(**args)
        self.nodes = {}
        self.nodeid = 0

    def start_output (self):
        """print start of checking info as gml comment"""
        linkcheck.logger.Logger.init(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field("intro"):
            self.fd.write("# "+(_("created by %s at %s") % \
                          (linkcheck.configuration.AppName,
                           linkcheck.strformat.strtime(self.starttime))))
            self.fd.write(os.linesep)
            self.fd.write("# "+(_("Get the newest version at %(url)s") %\
                               {'url': linkcheck.configuration.Url}))
            self.fd.write(os.linesep)
            self.fd.write("# "+(_("Write comments and bugs to %(email)s") % \
                            {'email': linkcheck.configuration.Email}))
            self.fd.write(os.linesep)
            self.fd.write(os.linesep)
            self.fd.write("graph [")
            self.fd.write(os.linesep)
            self.fd.write("  directed 1")
            self.fd.write(os.linesep)
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
            self.fd.write("  node [")
            self.fd.write(os.linesep)
            self.fd.write("    id     %d" % node.id)
            self.fd.write(os.linesep)
            if self.has_field("realurl"):
                self.fd.write('    label  "%s"' % node.url)
                self.fd.write(os.linesep)
            if node.dltime >= 0 and self.has_field("dltime"):
                self.fd.write("    dltime %d" % node.dltime)
                self.fd.write(os.linesep)
            if node.dlsize >= 0 and self.has_field("dlsize"):
                self.fd.write("    dlsize %d" % node.dlsize)
                self.fd.write(os.linesep)
            if node.checktime and self.has_field("checktime"):
                self.fd.write("    checktime %d" % node.checktime)
                self.fd.write(os.linesep)
            if self.has_field("extern"):
                self.fd.write("    extern %d" % (node.extern and 1 or 0))
                self.fd.write(os.linesep)
            self.fd.write("  ]")
            self.fd.write(os.linesep)
        self.write_edges()

    def write_edges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
        """
        for node in self.nodes.values():
            if self.nodes.has_key(node.parent_url):
                self.fd.write("  edge [")
                self.fd.write(os.linesep)
                self.fd.write('    label  "%s"' % node.base_url)
                self.fd.write(os.linesep)
                if self.has_field("parenturl"):
                    self.fd.write("    source %d" % \
                                  self.nodes[node.parent_url].id)
                    self.fd.write(os.linesep)
                self.fd.write("    target %d" % node.id)
                self.fd.write(os.linesep)
                if self.has_field("result"):
                    self.fd.write("    valid  %d" % (node.valid and 1 or 0))
                    self.fd.write(os.linesep)
                self.fd.write("  ]")
                self.fd.write(os.linesep)
        self.flush()

    def end_output (self, linknumber=-1):
        """print end of checking info as gml comment"""
        if self.fd is None:
            return
        self.fd.write("]")
        self.fd.write(os.linesep)
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write("# "+_("Stopped checking at %s (%s)")%\
                          (linkcheck.strformat.strtime(self.stoptime),
                           linkcheck.strformat.strduration(duration)))
            self.fd.write(os.linesep)
        self.flush()
        self.fd = None
