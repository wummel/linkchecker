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
import sys
try:
    import win32com
    import pythoncom
    has_win32com = True
    Error = pythoncom.com_error
except ImportError:
    has_win32com = False
    Error = StandardError


def main_is_frozen ():
    return hasattr(sys, "frozen")


def init_win32com ():
    """Initialize the win32com.client cache."""
    import win32com.client
    if win32com.client.gencache.is_readonly:
        #allow gencache to create the cached wrapper objects
        win32com.client.gencache.is_readonly = False
        # under py2exe the call in gencache to __init__() does not happen
        # so we use Rebuild() to force the creation of the gen_py folder
        if main_is_frozen():
            # The python...\win32com.client.gen_py dir must not exist
            # to allow creation of the cache in %temp% for py2exe.
            pass # XXX
        win32com.client.gencache.Rebuild()


def _init ():
    if has_win32com:
        init_win32com()
_init()



_has_app_cache = {}
def has_word ():
    """Determine if Word is available on the current system."""
    if not has_win32com:
        return False
    try:
        import _winreg
        key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "Word.Application")
        _winreg.CloseKey(key)
        return True
    except (EnvironmentError, ImportError):
        pass
    return False


def get_word_app ():
    """Return open Word.Application handle, or None if Word is not available
    on this system."""
    if not has_word():
        return None
    # Since this function is called from different threads, initialize
    # the COM layer.
    pythoncom.CoInitialize()
    import win32com.client
    app = win32com.client.gencache.EnsureDispatch("Word.Application")
    app.Visible = False
    return app


def close_word_app (app):
    app.Quit()


def open_wordfile (app, filename):
    return app.Documents.Open(filename)


def close_wordfile (doc):
    doc.Close()
