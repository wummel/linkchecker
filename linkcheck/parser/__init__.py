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
from .. import winutil, fileutil, log, LOG_CHECK, strformat
from ..htmlutil import linkparse
from ..HtmlParser import htmlsax
from ..bookmarks import firefox


def parse_url(url_data):
    """Parse a URL."""
    if url_data.is_directory():
        # both ftp and file links present directories as HTML data
        return parse_html(url_data)
    if url_data.is_file() and firefox.has_sqlite and firefox.extension.search(url_data.url):
        return parse_firefox(url_data)
    # determine parse routine according to content types
    mime = url_data.content_type
    key = url_data.ContentMimetypes[mime]
    return globals()["parse_"+key](url_data)


def parse_html (url_data):
    """Parse into HTML content and search for URLs to check.
    Found URLs are added to the URL queue.
    """
    find_links(url_data, url_data.add_url, linkparse.LinkTags)


def parse_opera (url_data):
    """Parse an opera bookmark file."""
    from ..bookmarks.opera import parse_bookmark_data
    for url, name, lineno in parse_bookmark_data(url_data.get_content()):
        url_data.add_url(url, line=lineno, name=name)


def parse_chromium (url_data):
    """Parse a Chromium or Google Chrome bookmark file."""
    from ..bookmarks.chromium import parse_bookmark_data
    for url, name in parse_bookmark_data(url_data.get_content()):
        url_data.add_url(url, name=name)


def parse_safari (url_data):
    """Parse a Safari bookmark file."""
    from ..bookmarks.safari import parse_bookmark_data
    for url, name in parse_bookmark_data(url_data.get_content()):
        url_data.add_url(url, name=name)


def parse_text (url_data):
    """Parse a text file with one url per line; comment and blank
    lines are ignored."""
    lineno = 0
    for line in url_data.get_content().splitlines():
        lineno += 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        url_data.add_url(line, line=lineno)


def parse_css (url_data):
    """
    Parse a CSS file for url() patterns.
    """
    lineno = 0
    linkfinder = linkparse.css_url_re.finditer
    strip_comments = linkparse.strip_c_comments
    for line in strip_comments(url_data.get_content()).splitlines():
        lineno += 1
        for mo in linkfinder(line):
            column = mo.start("url")
            url = strformat.unquote(mo.group("url").strip())
            url_data.add_url(url, line=lineno, column=column)


def parse_swf (url_data):
    """Parse a SWF file for URLs."""
    linkfinder = linkparse.swf_url_re.finditer
    for mo in linkfinder(url_data.get_content()):
        url = mo.group()
        url_data.add_url(url)


def parse_word (url_data):
    """Parse a word file for hyperlinks."""
    if not winutil.has_word():
        return
    filename = get_temp_filename()
    # open word file and parse hyperlinks
    try:
        app = winutil.get_word_app()
        try:
            doc = winutil.open_wordfile(app, filename)
            if doc is None:
                raise winutil.Error("could not open word file %r" % filename)
            try:
                for link in doc.Hyperlinks:
                    url_data.add_url(link.Address, name=link.TextToDisplay)
            finally:
                winutil.close_wordfile(doc)
        finally:
            winutil.close_word_app(app)
    except winutil.Error as msg:
        log.warn(LOG_CHECK, "Error parsing word file: %s", msg)


def parse_wml (url_data):
    """Parse into WML content and search for URLs to check.
    Found URLs are added to the URL queue.
    """
    find_links(url_data, url_data.add_url, linkparse.WmlTags)


def get_temp_filename (content):
    """Get temporary filename for content to parse."""
    # store content in temporary file
    fd, filename = fileutil.get_temp_file(mode='wb', suffix='.doc',
        prefix='lc_')
    try:
        fd.write(content)
    finally:
        fd.close()
    return filename


def find_links (url_data, callback, tags):
    """Parse into content and search for URLs to check.
    Found URLs are added to the URL queue.
    """
    # construct parser object
    handler = linkparse.LinkFinder(callback, tags)
    parser = htmlsax.parser(handler)
    if url_data.charset:
        parser.encoding = url_data.charset
    handler.parser = parser
    # parse
    try:
        parser.feed(url_data.get_content())
        parser.flush()
    except linkparse.StopParse as msg:
        log.debug(LOG_CHECK, "Stopped parsing: %s", msg)
        pass
    # break cyclic dependencies
    handler.parser = None
    parser.handler = None


def parse_firefox (url_data):
    """Parse a Firefox3 bookmark file."""
    filename = url_data.get_os_filename()
    for url, name in firefox.parse_bookmark_file(filename):
        url_data.add_url(url, name=name)


from .sitemap import parse_sitemap, parse_sitemapindex
