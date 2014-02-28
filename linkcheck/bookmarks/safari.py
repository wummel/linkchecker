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
import plistlib
try:
    import biplist
    has_biplist = True
except ImportError:
    has_biplist = False


def get_profile_dir ():
    """Return path where all profiles of current user are stored."""
    basedir = unicode(os.environ["HOME"])
    return os.path.join(basedir, u"Library", u"Safari")


def find_bookmark_file ():
    """Return the bookmark file of the Default profile.
    Returns absolute filename if found, or empty string if no bookmark file
    could be found.
    """
    if sys.platform != 'darwin':
        return u""
    try:
        dirname = get_profile_dir()
        if os.path.isdir(dirname):
            fname = os.path.join(dirname, u"Bookmarks.plist")
            if os.path.isfile(fname):
                return fname
    except Exception:
        pass
    return u""


def parse_bookmark_file (filename):
    """Return iterator for bookmarks of the form (url, name).
    Bookmarks are not sorted.
    """
    return parse_plist(get_plist_data_from_file(filename))


def parse_bookmark_data (data):
    """Return iterator for bookmarks of the form (url, name).
    Bookmarks are not sorted.
    """
    return parse_plist(get_plist_data_from_string(data))


def get_plist_data_from_file (filename):
    """Parse plist data for a file. Tries biplist, falling back to
    plistlib."""
    if has_biplist:
        return biplist.readPlist(filename)
    # fall back to normal plistlist
    try:
        return plistlib.readPlist(filename)
    except Exception:
        # not parseable (eg. not well-formed, or binary)
        return {}


def get_plist_data_from_string (data):
    """Parse plist data for a string. Tries biplist, falling back to
    plistlib."""
    if has_biplist:
        return biplist.readPlistFromString(data)
    # fall back to normal plistlist
    try:
        return plistlib.readPlistFromString(data)
    except Exception:
        # not parseable (eg. not well-formed, or binary)
        return {}


# some key strings
KEY_URLSTRING = 'URLString'
KEY_URIDICTIONARY = 'URIDictionary'
KEY_CHILDREN = 'Children'
KEY_WEBBOOKMARKTYPE = 'WebBookmarkType'

def parse_plist(entry):
    """Parse a XML dictionary entry."""
    if is_leaf(entry):
        url = entry[KEY_URLSTRING]
        title = entry[KEY_URIDICTIONARY].get('title', url)
        yield (url, title)
    elif has_children(entry):
        for child in entry[KEY_CHILDREN]:
            for item in parse_plist(child):
                yield item


def is_leaf (entry):
    """Return true if plist entry is an URL entry."""
    return entry.get(KEY_WEBBOOKMARKTYPE) == 'WebBookmarkTypeLeaf'


def has_children (entry):
    """Return true if plist entry has children."""
    return entry.get(KEY_WEBBOOKMARKTYPE) == 'WebBookmarkTypeList'
