# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2006  Bastian Kleineidam
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
General navigation writer reading .nav file info.
"""

import sys
import os
import re
from cStringIO import StringIO

_slashes_ro = re.compile(r"/+")
_thisdir_ro = re.compile(r"^\./")
_samedir_ro = re.compile(r"/\./|/\.$")
_parentdir_ro = re.compile(r"^/(\.\./)+|/(?!\.\./)[^/]+/\.\.(/|$)")
_relparentdir_ro = re.compile(r"^(?!\.\./)[^/]+/\.\.(/|$)")
def collapse_segments (path):
    """
    Remove all redundant segments from the given URL path.
    Precondition: path is an unquoted url path
    """
    # shrink multiple slashes to one slash
    path = _slashes_ro.sub("/", path)
    # collapse redundant path segments
    path = _thisdir_ro.sub("", path)
    path = _samedir_ro.sub("/", path)
    # collapse parent path segments
    # note: here we exploit the fact that the replacements happen
    # to be from left to right (see also _parentdir_ro above)
    newpath = _parentdir_ro.sub("/", path)
    while newpath != path:
        path = newpath
        newpath = _parentdir_ro.sub("/", path)
    # collapse parent path segments of relative paths
    # (ie. without leading slash)
    newpath = _relparentdir_ro.sub("", path)
    while newpath != path:
        path = newpath
        newpath = _relparentdir_ro.sub("", path)
    return path


class Node (object):
    """
    Node class for use in a navigation tree, with abilities to write
    HTML output.
    """

    def __init__ (self, name, order, filename):
        """Initialize node information"""
        self.name = name
        self.order = order
        self.filename = filename
        self.level = 0
        self.children = []
        self.sibling_right = None
        self.active = False
        self.parent = None

    def get_url (self, level):
        """Get relative URL to this node."""
        if self.children:
            url = self.children[0].get_url(level)
        else:
            url = "../"*level + self.filename
        return collapse_segments(url)

    def addChildren (self, nodes):
        """
        Add given nodes as children of this node, setting parent
        and level information accordingly.
        """
        for node in nodes:
            node.parent = self
            node.level = self.level + 1
            self.children.append(node)

    def write_nav (self, fp, active):
        """
        Write HTML node navigation.
        """
        descend = has_node(active, self.children)
        if self.active or descend:
            self.write_active(fp)
        else:
            self.write_inactive(fp, active.level)
        if self.sibling_right:
            self.sibling_right.write_nav(fp, active)
        if descend:
            # go to next level
            self.write_nextlevel(fp)
            self.children[0].write_nav(fp, active)

    def write_inactive (self, fp, level):
        """
        Write HTML of inactive navigation node.
        """
        s = '<a href="%s">%s' % (self.get_url(level), self.name)
        if self.children:
            s += ' &gt;'
        s += "</a>\n"
        fp.write(s)

    def write_active (self, fp):
        """
        Write HTML of active navigation node.
        """
        s = "<span>"
        #if not self.children:
        #    s += '&gt; '
        s += self.name
        if self.children:
            s += ' &gt;'
        s += "</span>\n"
        fp.write(s)

    def write_nextlevel (self, fp):
        fp.write('</div>\n<div class="navrow" style="padding: 0em 0em 0em %dem;">'% (self.level+2))

    def new_node (self):
        return Node(self.name, sys.maxint, self.filename)

    def __repr__ (self):
        return "<Node %r>"%self.name

    def __lt__(self, other):
        return self.order < other.order

    def __le__(self, other):
        return self.order <= other.order

    def __eq__(self, other):
        return self.order == other.order

    def __ne__(self, other):
        return self.order != other.order

    def __gt__(self, other):
        return self.order > other.order

    def __ge__(self, other):
        return self.order >= other.order


def parse_navtree (dirname):
    """
    Parse a hierarchy of .nav files into a tree structure,
    consisting of lists of lists. The list entries are sorted in
    navigation order.
    """
    nodes = []
    files = os.listdir(dirname)
    for f in files:
        filename = os.path.join(dirname, f)
        htmlname = os.path.join(dirname, os.path.splitext(f)[0]+".html")
        if os.path.isfile(filename) and os.path.isfile(htmlname) and \
           f.endswith('.nav'):
            nodes.append(get_nav_node(filename, htmlname))
        elif os.path.isdir(filename):
            subnodes = parse_navtree(filename)
            if subnodes:
                if os.path.isfile(filename+".nav"):
                    node = get_nav_node(filename+".nav", filename)
                else:
                    node = subnodes[0].new_node()
                node.addChildren(subnodes)
                nodes.append(node)
    nodes.sort()
    for i,n in enumerate(nodes):
        if (i+1)<len(nodes):
            n.sibling_right = nodes[i+1]
    #print_nodes(nodes)
    return nodes


def get_nav_node (navfile, htmlname):
    """
    Get a Node() instance with info of given navfile.
    """
    flocals = {}
    execfile(navfile, {}, flocals)
    order = flocals.get('order', sys.maxint)
    name = flocals['name']
    return Node(name, order, htmlname)


def print_nodes (nodes):
    """
    Print a tree structure to stdout.
    """
    for node in nodes:
        print " "*node.level+node.name
        if node.children:
            print_nodes(node.children)


def has_node (node, nodes):
    """
    Look for node in a tree structure.

    @return True if node is found
    """
    for n in nodes:
        if node.filename == n.filename:
            return True
        if has_node(node, n.children):
            return True
    return False


def generate_nav (start, nodes):
    """
    Write one navigation tree level into HTML files, with given
    start node as root node.
    """
    for node in nodes:
        print node.filename
        if node.children:
            generate_nav(start, node.children)
        else:
            node.active = True
            fp = StringIO()
            start.write_nav(fp, node)
            nav = """<div class="navigation">
<div class="navrow" style="padding: 0em 0em 0em 1em;">
%s
</div>
</div>
""" % fp.getvalue()
            node.active = False
            write_nav(node.filename, nav)


def write_nav (filename, nav):
    """
    Write navigation into filename.
    """
    lines = []
    skip = False
    f = open(filename)
    for line in f:
        if not skip:
            lines.append(line)
        if line.startswith("<!-- bfknav -->"):
            skip = True
            lines.append(nav)
        elif line.startswith("<!-- /bfknav -->"):
            skip = False
            lines.append(line)
    f.close()
    f = open(filename, 'w')
    for line in lines:
        f.write(line)
    f.close()


if __name__=='__main__':
    nodes = parse_navtree(".")
    if nodes:
        generate_nav(nodes[0], nodes)
