# -*- coding: iso-8859-1 -*-
# Copyright (C) 2011-2014 Bastian Kleineidam
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
import os

# Windows filename encoding
nt_filename_encoding="mbcs"

# List of possible Opera bookmark files.
OperaBookmarkFiles = (
  "bookmarks.adr", # for Opera >= 10.0
  "opera6.adr",
)


def get_profile_dir ():
    """Return path where all profiles of current user are stored."""
    if os.name == 'nt':
        basedir = unicode(os.environ["APPDATA"], nt_filename_encoding)
        dirpath = os.path.join(basedir, u"Opera", u"Opera")
    elif os.name == 'posix':
        basedir = unicode(os.environ["HOME"])
        dirpath = os.path.join(basedir, u".opera")
    return dirpath


def find_bookmark_file ():
    """Return the bookmark file of the Opera profile.
    Returns absolute filename if found, or empty string if no bookmark file
    could be found.
    """
    try:
        dirname = get_profile_dir()
        if os.path.isdir(dirname):
            for name in OperaBookmarkFiles:
                fname = os.path.join(dirname, name)
                if os.path.isfile(fname):
                    return fname
    except Exception:
        pass
    return u""


def parse_bookmark_data (data):
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
