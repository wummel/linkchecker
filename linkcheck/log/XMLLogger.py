# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2003  Bastian Kleineidam
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
from linkcheck import Config, i18n
from linkcheck.StringUtil import xmlify
from linkcheck.log import strtime
from StandardLogger import StandardLogger
from Logger import Logger

class XMLLogger (StandardLogger):
    """XML output mirroring the GML structure. Easy to parse with any XML
       tool."""
    def __init__ (self, **args):
        StandardLogger.__init__(self, **args)
        self.nodes = {}
        self.nodeid = 0

    def init (self):
        Logger.init(self)
        if self.fd is None: return
        self.starttime = time.time()
        self.fd.write('<?xml version="1.0"?>\n')
        if self.has_field("intro"):
            self.fd.write("<!--\n")
            self.fd.write("  "+i18n._("created by %s at %s\n") % \
	              (Config.AppName, strtime(self.starttime)))
            self.fd.write("  "+i18n._("Get the newest version at %s\n") % Config.Url)
            self.fd.write("  "+i18n._("Write comments and bugs to %s\n\n") % \
	              Config.Email)
            self.fd.write("-->\n\n")
	self.fd.write('<GraphXML>\n<graph isDirected="true">\n')
        self.fd.flush()

    def newUrl (self, urlData):
        """write one node and all possible edges"""
        if self.fd is None: return
        node = urlData
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.fd.write('  <node name="%d" ' % node.id)
            self.fd.write(">\n")
            if self.has_field("realurl"):
                self.fd.write("    <label>%s</label>\n" % xmlify(node.url))
            self.fd.write("    <data>\n")
            if node.dltime>=0 and self.has_field("dltime"):
                self.fd.write("      <dltime>%f</dltime>\n" % node.dltime)
            if node.dlsize>=0 and self.has_field("dlsize"):
                self.fd.write("      <dlsize>%d</dlsize>\n" % node.dlsize)
            if node.checktime and self.has_field("checktime"):
                self.fd.write("      <checktime>%f</checktime>\n" \
                              % node.checktime)
            if self.has_field("extern"):
                self.fd.write("      <extern>%d</extern>\n" % \
	                  (node.extern and 1 or 0))
            self.fd.write("    </data>\n")
	    self.fd.write("  </node>\n")
        self.writeEdges()

    def writeEdges (self):
        """write all edges we can find in the graph in a brute-force
           manner. Better would be a mapping of parent urls.
	"""
        for node in self.nodes.values():
            if self.nodes.has_key(node.parentName):
                self.fd.write("  <edge")
                self.fd.write(' source="%d"' % \
		              self.nodes[node.parentName].id)
                self.fd.write(' target="%d"' % node.id)
                self.fd.write(">\n")
                if self.has_field("url"):
		    self.fd.write("    <label>%s</label>\n" % xmlify(node.urlName))
                self.fd.write("    <data>\n")
                if self.has_field("result"):
                    self.fd.write("      <valid>%d</valid>\n" % \
		              (node.valid and 1 or 0))
                self.fd.write("    </data>\n")
                self.fd.write("  </edge>\n")
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        self.fd.write("</graph>\n</GraphXML>\n")
        if self.has_field("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = i18n._("seconds")
            self.fd.write("<!-- ")
            self.fd.write(i18n._("Stopped checking at %s") % strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = i18n._("minutes")
            if duration > 60:
                duration = duration / 60
                name = i18n._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
            self.fd.write("-->")
        self.fd.flush()
        self.fd = None

