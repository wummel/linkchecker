# Copyright (C) 2000-2002  Bastian Kleineidam
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

import time, linkcheck, linkcheck.Config
from linkcheck.StringUtil import xmlify
from linkcheck.log import strtime
from StandardLogger import StandardLogger

class XMLLogger (StandardLogger):
    """XML output mirroring the GML structure. Easy to parse with any XML
       tool."""
    def __init__ (self, **args):
        apply(StandardLogger.__init__, (self,), args)
        self.nodes = {}
        self.nodeid = 0

    def init (self):
        if self.fd is None: return
        self.starttime = time.time()
        self.fd.write('<?xml version="1.0"?>\n')
        if self.logfield("intro"):
            self.fd.write("<!--\n")
            self.fd.write("  "+linkcheck._("created by %s at %s\n") % \
	              (linkcheck.Config.AppName, strtime(self.starttime)))
            self.fd.write("  "+linkcheck._("Get the newest version at %s\n") % linkcheck.Config.Url)
            self.fd.write("  "+linkcheck._("Write comments and bugs to %s\n\n") % \
	              linkcheck.Config.Email)
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
            if self.logfield("realurl"):
                self.fd.write("    <label>%s</label>\n" % xmlify(node.url))
            self.fd.write("    <data>\n")
            if node.downloadtime and self.logfield("dltime"):
                self.fd.write("      <dltime>%f</dltime>\n" \
                                  % node.downloadtime)
            if node.checktime and self.logfield("checktime"):
                self.fd.write("      <checktime>%f</checktime>\n" \
                              % node.checktime)
            if self.logfield("extern"):
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
                if self.logfield("url"):
		    self.fd.write("    <label>%s</label>\n" % xmlify(node.urlName))
                self.fd.write("    <data>\n")
                if self.logfield("result"):
                    self.fd.write("      <valid>%d</valid>\n" % \
		              (node.valid and 1 or 0))
                self.fd.write("    </data>\n")
                self.fd.write("  </edge>\n")
        self.fd.flush()

    def endOfOutput (self, linknumber=-1):
        if self.fd is None: return
        self.fd.write("</graph>\n</GraphXML>\n")
        if self.logfield("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            name = linkcheck._("seconds")
            self.fd.write("<!-- ")
            self.fd.write(linkcheck._("Stopped checking at %s") % strtime(self.stoptime))
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("minutes")
            if duration > 60:
                duration = duration / 60
                name = linkcheck._("hours")
            self.fd.write(" (%.3f %s)\n" % (duration, name))
            self.fd.write("-->")
        self.fd.flush()
        self.fd = None

