# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005  Bastian Kleineidam
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
A DOT graph format logger. The specification has been taken from
http://www.graphviz.org/cvs/doc/info/lang.html.
"""

import time
import os

import linkcheck.configuration


class DOTLogger (linkcheck.logger.Logger):
    """
    Generates .dot sitemap graphs. Use graphviz to see the sitemap graph.
    """

    def __init__ (self, **args):
        """
        Initialize graph node list and internal id counter.
        """
        super(GMLLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def start_output (self):
        """
        Print start of checking info as DOT comment.
        """
        super(DOTLogger, self).start_output()
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
        self.writeln(u"graph {")
        self.flush()

    def comment (self, s, **args):
        """
        Print DOT comment.
        """
        self.write(u"// ")
        self.writeln(s=s, **args)

    def new_url (self, url_data):
        """
        Write one node and all possible edges.
        """
        if self.fd is None:
            return
        node = url_data
        if node.url and not self.nodes.has_key(node.url):
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.writeln(u"  %d [" % node.id)
            if self.has_field("realurl"):
                self.writeln(u'    label="%s",' % dotquote(node.url))
            if node.dltime >= 0 and self.has_field("dltime"):
                self.writeln(u"    dltime=%d," % node.dltime)
            if node.dlsize >= 0 and self.has_field("dlsize"):
                self.writeln(u"    dlsize=%d," % node.dlsize)
            if node.checktime and self.has_field("checktime"):
                self.writeln(u"    checktime=%d," % node.checktime)
            if self.has_field("extern"):
                self.writeln(u"    extern=%d," % (node.extern and 1 or 0))
            self.writeln(u"  ];")
        self.write_edges()

    def write_edges (self):
        """
        Write all edges we can find in the graph in a brute-force
        manner. Better would be a mapping of parent urls.
        """
        for node in self.nodes.values():
            if self.nodes.has_key(node.parent_url):
                source = self.nodes[node.parent_url].id
                target = node.id
                self.writeln(u"  %d -> %d [" % (source, target))
                self.writeln(u'    label="%s",' % dotquote(node.base_url))
                if self.has_field("result"):
                    self.writeln(u"    valid=%d," % (node.valid and 1 or 0))
                self.writeln(u"  ];")
        self.flush()

    def end_output (self, linknumber=-1):
        """
        Print end of checking info as DOT comment.
        """
        if self.fd is None:
            return
        self.writeln(u"}")
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


def dotquote (s):
    return s.replace('"', '\\"')
