""" linkcheck/FindUrlData.py

    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
from UrlData import UrlData
from linkcheck import _

class FindUrlData(UrlData):
    """Url link with find: scheme. This is found in Mozillas Technology
       demonstration links and searches for specific bookmarks.
       We just ignore this thing."""

    def check(self, config):
        self.setWarning(_("find: links are Mozilla-specific and will be ignored"))
        self.logMe(config)

    def get_scheme(self):
        return "find"
