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
"""Windows utility functions."""

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
