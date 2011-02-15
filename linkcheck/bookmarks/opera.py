# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011 Bastian Kleineidam
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


def parse_bookmarks (data):
    """Return iterator for bookmarks of the form (url, name, line number).
    Bookmarks are not sorted.
    """
    name = None
    lineno = 0
    for line in data.splitlines():
        lineno += 1
        line = line.strip()
        if line.startswith("NAME="):
            name = line[5:]
        elif line.startswith("URL="):
            url = line[4:]
            if url and name is not None:
                yield (url, name, lineno)
        else:
            name = None
