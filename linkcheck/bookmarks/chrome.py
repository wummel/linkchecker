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
import sys

# Windows filename encoding
nt_filename_encoding="mbcs"


def get_profile_dir ():
    """Return path where all profiles of current user are stored."""
    if os.name == 'nt':
        if "LOCALAPPDATA" in os.environ:
            basedir = unicode(os.environ["LOCALAPPDATA"], nt_filename_encoding)
        else:
            # read local appdata directory from registry
            from ..winutil import get_shell_folder
            try:
                basedir = get_shell_folder("Local AppData")
            except EnvironmentError:
                basedir = os.path.join(os.environ["USERPROFILE"], "Local Settings", "Application Data")
        dirpath = os.path.join(basedir, u"Google", u"Chrome", u"User Data")
    elif os.name == 'posix':
        basedir = unicode(os.environ["HOME"])
        if sys.platform == 'darwin':
            dirpath = os.path.join(basedir, u"Library", u"Application Support")
        else:
            dirpath = os.path.join(basedir, u".config")
        dirpath = os.path.join(dirpath, u"Google", u"Chrome")
    return dirpath


def find_bookmark_file (profile="Default"):
    """Return the bookmark file of the Default profile.
    Returns absolute filename if found, or empty string if no bookmark file
    could be found.
    """
    try:
        dirname = os.path.join(get_profile_dir(), profile)
        if os.path.isdir(dirname):
            fname = os.path.join(dirname, "Bookmarks")
            if os.path.isfile(fname):
                return fname
    except Exception:
        pass
    return u""


from .chromium import parse_bookmark_data, parse_bookmark_file
