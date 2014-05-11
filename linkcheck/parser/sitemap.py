# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
Main functions for link parsing
"""
from xml.parsers.expat import ParserCreate
from xml.parsers.expat import ExpatError
from ..checker.const import (WARN_XML_PARSE_ERROR)

class XmlTagUrlParser(object):
    """Parse XML files and find URLs in text content of a tag name."""

    def __init__(self, tag):
        """Initialize the parser."""
        self.tag = tag
        self.parser = ParserCreate()
        self.parser.buffer_text = True
        self.parser.returns_unicode = True
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data

    def parse(self, url_data):
        """Parse XML URL data."""
        self.url_data = url_data
        self.loc = False
        self.url = u""
        data = url_data.get_content()
        isfinal = True
        try:
            self.parser.Parse(data, isfinal)
        except ExpatError as expaterr:
            self.url_data.add_warning(expaterr.message,tag=WARN_XML_PARSE_ERROR)
    def start_element(self, name, attrs):
        """Set tag status for start element."""
        self.in_tag = (name == self.tag)
        self.url = u""

    def end_element(self, name):
        """If end tag is our tag, call add_url()."""
        self.in_tag = False
        if name == self.tag:
            self.add_url()

    def add_url(self):
        """Add non-empty URLs to the queue."""
        if self.url:
            self.url_data.add_url(self.url, line=self.parser.CurrentLineNumber,
                column=self.parser.CurrentColumnNumber)
            self.url = u""

    def char_data(self, data):
        """If inside the wanted tag, append data to URL."""
        if self.loc:
            self.url += data


def parse_sitemap(url_data):
    """Parse XML sitemap data."""
    XmlTagUrlParser(u"loc").parse(url_data)


def parse_sitemapindex(url_data):
    """Parse XML sitemap index data."""
    XmlTagUrlParser(u"loc").parse(url_data)

