# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
File and path utilities.
"""

import os
import re
import mimetypes

from . import log
from .logconf import LOG_CHECK

mimedb = None

def init_mimedb():
    """Initialize the local MIME database."""
    global mimedb
    try:
        mimedb = mimetypes.MimeTypes(strict=False)
    except Exception as msg:
        log.error(LOG_CHECK, "could not initialize MIME database: %s" % msg)
        return
    # For Opera bookmark files (opera6.adr)
    add_mimetype(mimedb, 'text/plain', '.adr')
    # To recognize PHP files as HTML with content check.
    add_mimetype(mimedb, 'application/x-httpd-php', '.php')
    # To recognize WML files
    add_mimetype(mimedb, 'text/vnd.wap.wml', '.wml')


def add_mimetype(mimedb, mimetype, extension):
    """Add or replace a mimetype to be used with the given extension."""
    # If extension is already a common type, strict=True must be used.
    strict = extension in mimedb.types_map[True]
    mimedb.add_type(mimetype, extension, strict=strict)


# if file extension lookup was unsuccessful, look at the content
PARSE_CONTENTS = {
    "text/html": re.compile(r'^(?i)<(!DOCTYPE html|html|head|title)'),
    "text/plain+opera": re.compile(r'^Opera Hotlist'),
    "text/plain+chromium": re.compile(r'^{\s*"checksum":'),
    "text/plain+linkchecker": re.compile(r'(?i)^# LinkChecker URL list'),
    "application/xml+sitemapindex": re.compile(r'(?i)<\?xml[^<]+<sitemapindex\s+'),
    "application/xml+sitemap": re.compile(r'(?i)<\?xml[^<]+<urlset\s+'),
}

def guess_mimetype (filename, read=None):
    """Return MIME type of file, or 'application/octet-stream' if it could
    not be determined."""
    mime, encoding = None, None
    if mimedb:
        mime, encoding = mimedb.guess_type(filename, strict=False)
    basename = os.path.basename(filename)
    # Special case for Safari Bookmark files
    if not mime and basename == 'Bookmarks.plist':
        return 'application/x-plist+safari'
    # Special case for Google Chrome Bookmark files.
    if not mime and basename == 'Bookmarks':
        mime = 'text/plain'
    # Some mime types can be differentiated further with content reading.
    if mime in ("text/plain", "application/xml", "text/xml") and read is not None:
        read_mime = guess_mimetype_read(read)
        if read_mime is not None:
            mime = read_mime
    if not mime:
        mime = "application/octet-stream"
    elif ";" in mime:
        # split off not needed extension info
        mime = mime.split(';')[0]
    return mime.strip().lower()


def guess_mimetype_read(read):
    """Try to read some content and do a poor man's file(1)."""
    mime = None
    try:
        data = read()[:70]
    except Exception:
        pass
    else:
        for cmime, ro in PARSE_CONTENTS.items():
            if ro.search(data):
                mime = cmime
                break
    return mime


init_mimedb()
