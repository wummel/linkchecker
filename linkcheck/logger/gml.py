# -*- coding: iso-8859-1 -*-
"""a gml logger"""
# Copyright (C) 2000-2005  Bastian Kleineidam
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

import linkcheck.configuration


class GMLLogger (linkcheck.logger.Logger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """

    def __init__ (self, **args):
        """initialize graph node list and internal id counter"""
        super(GMLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def start_output (self):
        """print start of checking info as gml comment"""
        super(GMLLogger, self).start_output()
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field("intro"):
            self.comment(_("created by %s at %s") % \
                         (linkcheck.configuration.AppName,
                          linkcheck.strformat.strtime(self.starttime)))
            self.comment(_("Get the newest version at %(url)s") % \
                         {'url': linkcheck.configuration.Url})
            self.comment(_("Write comments and bugs to %(email)s") % \
                         {'email': linkcheck.configuration.Email})
            self.check_date()
            self.writeln()
            self.writeln(u"graph [")
            self.writeln(u"  directed 1")
            self.flush()

    def comment (self, s, **args):
        """Print GML comment."""
        self.write(u"# ")
        self.writeln(s=s, **args)

    def new_url (self, url_data):
        """write one node and all possible edges"""
        if self.fd is None:
            return
        node = url_data
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.writeln(u"  node [")
            self.writeln(u"    id     %d" % node.id)
            if self.has_field("realurl"):
                self.writeln(u'    label  "%s"' % node.url)
            if node.dltime >= 0 and self.has_field("dltime"):
                self.writeln(u"    dltime %d" % node.dltime)
            if node.dlsize >= 0 and self.has_field("dlsize"):
                self.writeln(u"    dlsize %d" % node.dlsize)
            if node.checktime and self.has_field("checktime"):
                self.writeln(u"    checktime %d" % node.checktime)
            if self.has_field("extern"):
                self.writeln(u"    extern %d" % (node.extern and 1 or 0))
            self.writeln(u"  ]")
        self.write_edges()

    def write_edges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
        """
        for node in self.nodes.values():
            if self.nodes.has_key(node.parent_url):
                self.writeln(u"  edge [")
                self.writeln(u'    label  "%s"' % node.base_url)
                if self.has_field("parenturl"):
                    self.writeln(u"    source %d" % \
                                 self.nodes[node.parent_url].id)
                self.writeln(u"    target %d" % node.id)
                if self.has_field("result"):
                    self.writeln(u"    valid  %d" % (node.valid and 1 or 0))
                self.writeln(u"  ]")
        self.flush()

    def end_output (self, linknumber=-1):
        """print end of checking info as gml comment"""
        if self.fd is None:
            return
        self.writeln(u"]")
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %s (%s)")%\
                         (linkcheck.strformat.strtime(self.stoptime),
                          linkcheck.strformat.strduration(duration)))
        self.flush()
        if self.close_fd:
            self.fd.close()
        self.fd = None
