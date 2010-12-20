# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010 Bastian Kleineidam
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
import glob

# Windows filename encoding
nt_filename_encoding="mbcs"

def get_profile_dir ():
    """Return path where all profiles of current user are stored."""
    if os.name == 'nt':
        basedir = unicode(os.environ["APPDATA"], nt_filename_encoding)
        dirpath = os.path.join(basedir, u"Mozilla", u"Firefox", u"Profiles")
    elif os.name == 'posix':
        basedir = unicode(os.environ["HOME"])
        dirpath = os.path.join(basedir, u".mozilla", u"firefox")
    return dirpath


def find_bookmark_file ():
    """Return the first found places.sqlite file of the profile directories
    ending with '.default'.
    """
    for dirname in glob.glob(u"%s/*.default" % get_profile_dir()):
        if os.path.isdir(dirname):
            fname = os.path.join(dirname, "places.sqlite")
            if os.path.isfile(fname):
                return fname
    return u""
