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

imgtag_re = re.compile(r"""(?i)\s+alt\s*=\s*(?P<name>("[^"\n]*"|'[^'\n]*'|[^\s>]+))""")
img_re = re.compile(r"""(?i)<\s*img\s+("[^"\n]*"|'[^'\n]*'|[^>]+)+>""")
endtag_re = re.compile(r"""(?i)</a\s*>""")

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
    endtag = endtag_re.search(txt)
    if not endtag: return name
    name = txt[:endtag.start()]
    if img_re.search(name):
        return image_name(name)
    name = StringUtil.remove_markup(name)
    name = StringUtil.unhtmlify(name)
    return name

_tests = (
    "<img src='' alt=''></a>",
    "<img src alt=abc></a>",
    "<b>guru guru</a>",
    "a\njo</a>",
    "test<</a>",
    "test</</a>",
    "test</a</a>",
    "test",
    "\n",
    "",
    '"</a>"foo',
)

def _test ():
    for t in _tests:
        print repr(href_name(t))

if __name__=='__main__':
    _test()
