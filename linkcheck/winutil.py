# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
try:
    import win32com
    import pythoncom
    has_win32com = True
    Error = pythoncom.com_error
except ImportError:
    has_win32com = False
    Error = StandardError


def init_win32com ():
    """Initialize the win32com.client cache."""
    import win32com.client
    if win32com.client.gencache.is_readonly:
        #allow gencache to create the cached wrapper objects
        win32com.client.gencache.is_readonly = False
        # under py2exe the call in gencache to __init__() does not happen
        # so we use Rebuild() to force the creation of the gen_py folder
        # Note that the python...\win32com.client.gen_py dir must not exist
        # to allow creation of the cache in %temp% for py2exe.
        # This is ensured by excluding win32com.gen_py in setup.py
        win32com.client.gencache.Rebuild()


def _init ():
    """Initialize the win32com package."""
    if has_win32com:
        init_win32com()
_init()


_has_app_cache = {}
def has_word ():
    """Determine if Word is available on the current system."""
    if not has_win32com:
        return False
    try:
        import _winreg as winreg
    except ImportError:
        import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")
        winreg.CloseKey(key)
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
    """Close Word application object."""
    app.Quit()


def open_wordfile (app, filename):
    """Open given Word file with application object."""
    return app.Documents.Open(filename, ReadOnly=True,
      AddToRecentFiles=False, Visible=False, NoEncodingDialog=True)


def close_wordfile (doc):
    """Close word file."""
    doc.Close()


def get_shell_folder (name):
    """Get Windows Shell Folder locations from the registry."""
    try:
        import _winreg as winreg
    except ImportError:
        import winreg
    lm = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    try:
        key = winreg.OpenKey(lm, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        try:
            return winreg.QueryValueEx(key, name)[0]
        finally:
            key.Close()
    finally:
        lm.Close()
