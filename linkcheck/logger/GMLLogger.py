# -*- coding: iso-8859-1 -*-
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
import linkcheck.logger.StandardLogger
import bk.i18n


class GMLLogger (linkcheck.logger.StandardLogger.StandardLogger):
    """GML means Graph Modeling Language. Use a GML tool to see
    your sitemap graph.
    """

    def __init__ (self, **args):
        super(GMLLogger, self).__init__(**args)
        self.nodes = {}
        self.nodeid = 0

    def init (self):
        linkcheck.logger.Logger.Logger.init(self)
        if self.fd is None:
            return
        self.starttime = time.time()
        if self.has_field("intro"):
            self.fd.write("# "+(bk.i18n._("created by %s at %s\n") % (linkcheck.Config.AppName,
                      bk.strtime.strtime(self.starttime))))
            self.fd.write("# "+(bk.i18n._("Get the newest version at %s\n") % linkcheck.Config.Url))
            self.fd.write("# "+(bk.i18n._("Write comments and bugs to %s\n\n") % \
  	                    linkcheck.Config.Email))
            self.fd.write("graph [\n  directed 1\n")
            self.flush()

    def newUrl (self, urlData):
        """write one node and all possible edges"""
        if self.fd is None:
            return
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.fd.write("  node [\n")
	    self.fd.write("    id     %d\n" % node.id)
            if self.has_field("realurl"):
                self.fd.write('    label  "%s"\n' % node.url)
            if node.dltime>=0 and self.has_field("dltime"):
                self.fd.write("    dltime %d\n" % node.dltime)
            if node.dlsize>=0 and self.has_field("dlsize"):
                self.fd.write("    dlsize %d\n" % node.dlsize)
            if node.checktime and self.has_field("checktime"):
                self.fd.write("    checktime %d\n" % node.checktime)
            if self.has_field("extern"):
                self.fd.write("    extern %d\n" % (node.extern and 1 or 0))
	    self.fd.write("  ]\n")
        self.writeEdges()

    def writeEdges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  edge [\n")
		self.fd.write('    label  "%s"\n' % node.urlName)
                if self.has_field("parenturl"):
                    self.fd.write("    source %d\n" % \
	                          self.nodes[node.parentName].id)
                self.fd.write("    target %d\n" % node.id)
                if self.has_field("result"):
                    self.fd.write("    valid  %d\n" % (node.valid and 1 or 0))
                self.fd.write("  ]\n")
        self.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None:
            return
        self.fd.write("]\n")
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.fd.write("# "+bk.i18n._("Stopped checking at %s (%s)\n")%\
	                  (bk.strtime.strtime(self.stoptime),
                           bk.strtime.strduration(duration)))
        self.flush()
        self.fd = None
