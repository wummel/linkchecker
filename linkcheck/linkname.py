# Copyright (C) 2001  Bastian Kleineidam
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

import re, StringUtil

imgtag_re = re.compile("(?i)\s+alt\s*=\s*(?P<name>(\".*?\"|'.*?'|[^\s>]+))", re.DOTALL)
img_re = re.compile("(?i)<\s*img\s+.*>", re.DOTALL)
href_re = re.compile("(?i)(?P<name>.*?)</a\s*>", re.DOTALL)

def image_name(txt):
    name = ""
    mo = imgtag_re.search(txt)
    if mo:
        #print "DEBUG:", `mo.group(0)`
        name = StringUtil.stripQuotes(mo.group('name').strip())
        name = StringUtil.remove_markup(name)
        name = StringUtil.unhtmlify(name)
    #print "NAME:", `name`
    return name


def href_name(txt):
    name = ""
    mo = href_re.search(txt)
    if mo:
        #print "DEBUG:", `mo.group(0)`
        name = mo.group('name').strip()
        if img_re.search(name):
            name = image_name(name)
        name = StringUtil.remove_markup(name)
        name = StringUtil.unhtmlify(name)
    #print "NAME:", `name`
    return name
