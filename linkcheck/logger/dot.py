# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2008 Bastian Kleineidam
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
http://www.graphviz.org/doc/info/lang.html
"""

import time

import linkcheck.configuration


class DOTLogger (linkcheck.logger.Logger):
    """
    Generates .dot sitemap graphs. Use graphviz to see the sitemap graph.
    """

    def __init__ (self, **args):
        """
        Initialize graph node list and internal id counter.
        """
        super(DOTLogger, self).__init__(**args)
        self.init_fileoutput(args)
        self.nodes = {}
        self.nodeid = 0

    def start_output (self):
        """
        Write start of checking info as DOT comment.
        """
        super(DOTLogger, self).start_output()
        self.starttime = time.time()
        if self.has_part("intro"):
            self.comment(_("created by %(app)s at %(time)s") %
                        {"app": linkcheck.configuration.AppName,
                         "time": linkcheck.strformat.strtime(self.starttime)})
            self.comment(_("Get the newest version at %(url)s") %
                         {'url': linkcheck.configuration.Url})
            self.comment(_("Write comments and bugs to %(email)s") %
                         {'email': linkcheck.configuration.Email})
            self.check_date()
            self.writeln()
        self.writeln(u"digraph G {")
        self.flush()

    def comment (self, s, **args):
        """
        Write DOT comment.
        """
        self.write(u"// ")
        self.writeln(s=s, **args)

    def log_url (self, url_data):
        """
        Write one node and all possible edges.
        """
        node = url_data
        if node.url and node.url not in self.nodes:
            node.id = self.nodeid
            self.nodes[node.url] = node
            self.nodeid += 1
            self.writeln(u"  %d [" % node.id)
            if self.has_part("realurl"):
                self.writeln(u'    href="%s",' % dotquote(node.url))
            if node.dltime >= 0 and self.has_part("dltime"):
                self.writeln(u"    dltime=%d," % node.dltime)
            if node.dlsize >= 0 and self.has_part("dlsize"):
                self.writeln(u"    dlsize=%d," % node.dlsize)
            if node.checktime and self.has_part("checktime"):
                self.writeln(u"    checktime=%d," % node.checktime)
            if self.has_part("extern"):
                self.writeln(u"    extern=%d," % (1 if node.extern[0] else 0))
            self.writeln(u"  ];")

    def write_edges (self):
        """
        Write all edges we can find in the graph in a brute-force
        manner. Better would be a mapping of parent URLs.
        """
        for node in self.nodes.values():
            if node.parent_url in self.nodes:
                source = self.nodes[node.parent_url].id
                target = node.id
                self.writeln(u"  %d -> %d [" % (source, target))
                self.writeln(u'    label="%s",' % dotedge(node.name))
                if self.has_part("result"):
                    self.writeln(u"    valid=%d," % (1 if node.valid else 0))
                self.writeln(u"  ];")
        self.flush()

    def end_output (self):
        """
        Write end of checking info as DOT comment.
        """
        self.write_edges()
        self.writeln(u"}")
        if self.has_part("outro"):
            self.stoptime = time.time()
            duration = self.stoptime - self.starttime
            self.comment(_("Stopped checking at %(time)s (%(duration)s)") %
                 {"time": linkcheck.strformat.strtime(self.stoptime),
                  "duration": linkcheck.strformat.strduration_long(duration)})
        self.close_fileoutput()


def dotquote (s):
    """
    Escape disallowed characters in DOT format strings.
    """
    return s.replace('"', '\\"')


def dotedge (s):
    """
    Escape disallowed characters in DOT edge labels.
    """
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\l", "\\l")
    s = s.replace("\T", "\\T")
    s = s.replace("\H", "\\H")
    s = s.replace("\E", "\\E")
    return dotquote(s)
