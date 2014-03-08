# -*- coding: utf-8 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Test file parsing.
"""
import os
import sys
import zipfile
from tests import need_word
from . import LinkCheckTest, get_file


def unzip (filename, targetdir):
    """Unzip given zipfile into targetdir."""
    if isinstance(targetdir, unicode):
        targetdir = str(targetdir)
    zf = zipfile.ZipFile(filename)
    for name in zf.namelist():
        if name.endswith('/'):
            os.mkdir(os.path.join(targetdir, name), 0700)
        else:
            outfile = open(os.path.join(targetdir, name), 'wb')
            try:
                outfile.write(zf.read(name))
            finally:
                outfile.close()


class TestFile (LinkCheckTest):
    """
    Test file:// link checking (and file content parsing).
    """

    def test_html (self):
        self.file_test("file.html")

    def test_wml (self):
        self.file_test("file.wml")

    def test_text (self):
        self.file_test("file.txt")

    def test_asc (self):
        self.file_test("file.asc")

    def test_css (self):
        self.file_test("file.css")

    def test_php (self):
        self.file_test("file.php")

    @need_word
    def test_word (self):
        self.file_test("file.doc")

    def test_urllist (self):
        self.file_test("urllist.txt")

    def test_directory_listing (self):
        # unpack non-unicode filename which cannot be stored
        # in the SF subversion repository
        if os.name != 'posix' or sys.platform != 'linux2':
            return
        dirname = get_file("dir")
        if not os.path.isdir(dirname):
            unzip(dirname + ".zip", os.path.dirname(dirname))
        self.file_test("dir")

    def test_unicode_filename (self):
        # a unicode filename
        self.file_test(u"Мошкова.bin")

    def test_good_file (self):
        url = u"file://%(curdir)s/%(datadir)s/file.txt" % self.get_attrs()
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_bad_file (self):
        if os.name == 'nt':
            # Fails on NT platforms and I am too lazy to fix
            # Cause: url get quoted %7C which gets lowercased to
            # %7c and this fails.
            return
        url = u"file:/%(curdir)s/%(datadir)s/file.txt" % self.get_attrs()
        nurl = self.norm(url)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"error",
        ]
        self.direct(url, resultlines)

    def test_good_file_missing_dslash (self):
        # good file (missing double slash)
        attrs = self.get_attrs()
        url = u"file:%(curdir)s/%(datadir)s/file.txt" % attrs
        resultlines = [
            u"url %s" % url,
            u"cache key file://%(curdir)s/%(datadir)s/file.txt" % attrs,
            u"real url file://%(curdir)s/%(datadir)s/file.txt" % attrs,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_good_dir (self):
        url = u"file://%(curdir)s/%(datadir)s/" % self.get_attrs()
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % url,
            u"real url %s" % url,
            u"valid",
        ]
        self.direct(url, resultlines)

    def test_good_dir_space (self):
        url = u"file://%(curdir)s/%(datadir)s/a b/" % self.get_attrs()
        nurl = self.norm(url)
        url2 = u"file://%(curdir)s/%(datadir)s/a b/el.html" % self.get_attrs()
        nurl2 = self.norm(url2)
        url3 = u"file://%(curdir)s/%(datadir)s/a b/t.txt" % self.get_attrs()
        nurl3 = self.norm(url3)
        resultlines = [
            u"url %s" % url,
            u"cache key %s" % nurl,
            u"real url %s" % nurl,
            u"valid",
            u"url el.html",
            u"cache key %s" % nurl2,
            u"real url %s" % nurl2,
            u"name el.html",
            u"valid",
            u"url t.txt",
            u"cache key %s" % nurl3,
            u"real url %s" % nurl3,
            u"name t.txt",
            u"valid",
            u"url t.txt",
            u"cache key %s" % nurl3,
            u"real url %s" % nurl3,
            u"name External link",
            u"valid",
        ]
        self.direct(url, resultlines, recursionlevel=2)
