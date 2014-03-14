#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2012-2014 Bastian Kleineidam
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
Analyze a memory dump by the meliae module.
"""
import sys
import os
import codecs
import cgi
from linkcheck import strformat

def main (filename):
    om = print_memorydump(filename)
    dirname, basename = os.path.split(filename)
    basename = os.path.splitext(basename)[0]
    basedir = os.path.join(dirname, basename)
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    write_htmlfiles(om, basedir)

def print_memorydump(filename):
    from meliae import loader
    om = loader.load(filename, collapse=True)
    om.remove_expensive_references()
    print om.summarize()
    return om

def write_htmlfiles(om, basedir):
    om.compute_parents()
    open_files = {}
    for obj in om.objs.itervalues():
        fp = get_file(obj.type_str, open_files, basedir)
        write_html_obj(fp, obj, om.objs)
    close_files(open_files)

def get_file(type_str, open_files, basedir):
    """Get already opened file, or open and initialize a new one."""
    if type_str not in open_files:
        filename = type_str+".html"
        encoding = 'utf-8'
        fd = codecs.open(os.path.join(basedir, filename), 'w', encoding)
        open_files[type_str] = fd
        write_html_header(fd, type_str, encoding)
    return open_files[type_str]

def close_files(open_files):
    for fp in open_files.values():
        write_html_footer(fp)
        fp.close()

HtmlHeader = u"""
<!doctype html>
<head>
    <meta charset="%s">
</head>
<body>
"""

def write_html_header(fp, type_str, encoding):
    fp.write(HtmlHeader % encoding)
    fp.write(u"<h1>Type %s</h1>\n" % type_str)
    fp.write(u"<table><tr><th>Address</th><th>Name</th><th>Size</th><th>Parents</th><th>References</th></tr>\n")

def get_children(obj, objs):
    res = []
    for address in obj.children:
        if address in objs:
            child = objs[address]
            url = u"#%d" % address
            if child.type_str != obj.type_str:
                url = child.type_str + u".html" + url
            entry = u'<a href="%s">%d</a>' % (url, address)
        else:
            entry = u"%d" % address
        res.append(entry)
    return res

def get_parents(obj, objs):
    res = []
    for address in obj.parents:
        if address in objs:
            parent = objs[address]
            url = u"#%d" % address
            if parent.type_str != obj.type_str:
                url = parent.type_str + u".html" + url
            entry = u'<a href="%s">%d</a>' % (url, address)
        else:
            entry = u"%d" % address
        res.append(entry)
    return res

def write_html_obj(fp, obj, objs):
    if obj.value is None:
        value = u"None"
    else:
        value = cgi.escape(str(obj.value))
    attrs = dict(
        address=obj.address,
        size=strformat.strsize(obj.size),
        children=u",".join(get_children(obj, objs)),
        parents=u",".join(get_parents(obj, objs)),
        value=value,
    )
    fp.write(u"<tr><td>%(address)d</td><td>%(value)s</td><td>%(size)s</td><td>%(children)s</td></tr>\n" % attrs)

def write_html_footer(fp):
    fp.write(u"</table></body></html>")

if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
