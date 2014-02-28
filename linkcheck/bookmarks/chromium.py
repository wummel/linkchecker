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
import json


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
        dirpath = os.path.join(basedir, u"Chromium", u"User Data")
    elif os.name == 'posix':
        basedir = unicode(os.environ["HOME"])
        if sys.platform == 'darwin':
            dirpath = os.path.join(basedir, u"Library", u"Application Support")
        else:
            dirpath = os.path.join(basedir, u".config")
        dirpath = os.path.join(dirpath, u"chromium")
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


def parse_bookmark_data (data):
    """Parse data string.
    Return iterator for bookmarks of the form (url, name).
    Bookmarks are not sorted.
    """
    for url, name in parse_bookmark_json(json.loads(data)):
        yield url, name


def parse_bookmark_file (file):
    """Parse file object.
    Return iterator for bookmarks of the form (url, name).
    Bookmarks are not sorted.
    """
    for url, name in parse_bookmark_json(json.load(file)):
        yield url, name


def parse_bookmark_json (data):
    """Parse complete JSON data for Chromium Bookmarks."""
    for entry in data["roots"].values():
        for url, name in parse_bookmark_node(entry):
            yield url, name


def parse_bookmark_node (node):
    """Parse one JSON node of Chromium Bookmarks."""
    if node["type"] == "url":
        yield node["url"], node["name"]
    elif node["type"] == "folder":
        for child in node["children"]:
            for entry in parse_bookmark_node(child):
                yield entry
