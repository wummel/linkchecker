# -*- coding: utf-8 -*-
# Copyright (C) 2004-2012 Bastian Kleineidam
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
"""
Test bookmark file parsing.
"""
from . import LinkCheckTest
from .. import need_network, need_biplist
import os


class TestBookmarks (LinkCheckTest):
    """
    Test bookmark link checking and content parsing.
    """

    @need_network
    def _test_firefox_bookmarks (self):
        # firefox 3 bookmark file parsing
        self.file_test("places.sqlite")

    @need_network
    def _test_opera_bookmarks (self):
        # Opera bookmark file parsing
        self.file_test("opera6.adr")

    @need_network
    def _test_chromium_bookmarks (self):
        # Chromium and Google Chrome bookmark file parsing
        self.file_test("Bookmarks")

    @need_network
    def test_safari_bookmarks_xml (self):
        # Safari bookmark file parsing (for plaintext plist files)
        self.file_test(os.path.join("plist_xml", "Bookmarks.plist"))

    @need_network
    @need_biplist
    def test_safari_bookmarks_binary (self):
        # Safari bookmark file parsing (for binary plist files)
        self.file_test(os.path.join("plist_binary", "Bookmarks.plist"))
