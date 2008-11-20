# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Handle local file: links.
"""

import re
import os
import time
import urlparse
import urllib
import urllib2

from . import urlbase, get_index_html, absolute_url, get_url_from
from .. import log, LOG_CHECK, fileutil, strformat, url as urlutil
from .const import WARN_FILE_MISSING_SLASH, WARN_FILE_SYSTEM_PATH, \
    PARSE_EXTENSIONS, PARSE_CONTENTS

try:
    import sqlite3
    has_sqlite = True
except ImportError:
    has_sqlite = False

def get_files (dirname):
    """
    Get lists of files in directory. Does only allow regular files
    and directories, no symlinks.
    """
    files = []
    for entry in os.listdir(dirname):
        fullentry = os.path.join(dirname, entry)
        if os.path.islink(fullentry) or \
           not (os.path.isfile(fullentry) or os.path.isdir(fullentry)):
            continue
        files.append(entry)
    return files


def prepare_urlpath_for_nt (path):
    """
    URLs like 'file://server/path/' result in a path named '/server/path'.
    However urllib.url2pathname expects '////server/path'.
    """
    if '|' not in path:
        return "////"+path.lstrip("/")
    return path


def get_nt_filename (path):
    """
    Return case sensitive filename for NT path.
    """
    head, tail = os.path.split(path)
    if not tail:
        return path
    for fname in os.listdir(head):
        if fname.lower() == tail.lower():
            return os.path.join(get_nt_filename(head), fname)
    log.error(LOG_CHECK, "could not find %r in %r", tail, head)
    return path


def is_absolute_path (path):
    """Check if given path is absolute. On Windows absolute paths start
    with a drive letter. On all other systems absolute paths start with
    a slash."""
    if os.name == 'nt':
       return re.search(r"^[a-zA-Z]:", path)
    return path.startswith("/")


firefox_extension = re.compile(r'/(?i)places.sqlite$')

class FileUrl (urlbase.UrlBase):
    """
    Url link with file scheme.
    """

    def init (self, base_ref, base_url, parent_url, recursion_level,
              aggregate, line, column, name):
        """
        Besides the usual initialization the URL is normed according
        to the platform:
         - the base URL is made an absolute file:// URL
         - under Windows platform the drive specifier is normed
        """
        super(FileUrl, self).init(base_ref, base_url, parent_url,
                               recursion_level, aggregate, line, column, name)
        if self.base_url is None:
            return
        base_url = self.base_url
        if not (parent_url or base_ref or base_url.startswith("file:")):
            base_url = os.path.expanduser(base_url)
            if not is_absolute_path(base_url):
                base_url = os.getcwd()+"/"+base_url
            base_url = "file://"+base_url
        if os.name == "nt":
            base_url = base_url.replace("\\", "/")
            # transform c:/windows into /c|/windows
            base_url = re.sub("^file://(/?)([a-zA-Z]):", r"file:///\2|", base_url)
        # norm base url again after changing
        if self.base_url != base_url:
            base_url, is_idn = urlbase.url_norm(base_url)
            if is_idn:
                pass # XXX warn about idn use
            self.base_url = unicode(base_url)

    def build_url (self):
        """
        Calls super.build_url() and adds a trailing slash to directories.
        """
        super(FileUrl, self).build_url()
        # ignore query and fragment url parts for filesystem urls
        self.urlparts[3] = self.urlparts[4] = ''
        if self.is_directory() and not self.urlparts[2].endswith('/'):
            self.add_warning(_("Added trailing slash to directory."),
                           tag=WARN_FILE_MISSING_SLASH)
            self.urlparts[2] += '/'
        self.url = urlparse.urlunsplit(self.urlparts)

    def check_connection (self):
        """
        Try to open the local file. Under NT systems the case sensitivity
        is checked.
        """
        if self.is_directory():
            self.set_result(_("directory"))
        else:
            url = fileutil.pathencode(self.url)
            self.url_connection = urllib2.urlopen(url)
            self.check_case_sensitivity()

    def check_case_sensitivity (self):
        """
        Check if url and windows path name match cases
        else there might be problems when copying such
        files on web servers that are case sensitive.
        """
        if os.name != 'nt':
            return
        path = self.get_os_filename()
        realpath = get_nt_filename(path)
        if path != realpath:
            self.add_warning(_("The URL path %(path)r is not the same as the "
                            "system path %(realpath)r. You should always use "
                            "the system path in URLs.") % \
                            {"path": path, "realpath": realpath},
                               tag=WARN_FILE_SYSTEM_PATH)

    def get_content (self):
        """
        Return file content, or in case of directories a dummy HTML file
        with links to the files.
        """
        if not self.valid:
            return ""
        if self.data is not None:
            return self.data
        elif self.is_directory():
            return self.get_directory_content()
        else:
            return super(FileUrl, self).get_content()

    def get_directory_content (self):
        """
        Get dummy HTML data for the directory content.

        @return: HTML data
        @rtype: string
        """
        t = time.time()
        files = get_files(self.get_os_filename())
        data = get_index_html(files)
        self.data = data.encode("iso8859-1", "ignore")
        self.dltime = time.time() - t
        self.dlsize = len(self.data)
        return self.data

    def is_html (self):
        """
        Check if file is a HTML file.
        """
        if PARSE_EXTENSIONS['html'].search(self.url):
            return True
        if PARSE_CONTENTS['html'].search(self.get_content()):
            return True
        return False

    def is_css (self):
        """
        Check if file is a CSS file.
        """
        return bool(PARSE_EXTENSIONS['css'].search(self.url))

    def is_file (self):
        """
        This is a file.

        @return: True
        @rtype: bool
        """
        return True

    def get_os_filename (self):
        """
        Construct os specific file path out of the file:// URL.

        @return: file name
        @rtype: string
        """
        path = self.urlparts[2]
        if os.name == 'nt':
            path = prepare_urlpath_for_nt(path)
        return fileutil.pathencode(urllib.url2pathname(path))

    def is_directory (self):
        """
        Check if file is a directory.

        @return: True iff file is a directory
        @rtype: bool
        """
        filename = self.get_os_filename()
        return os.path.isdir(filename) and not os.path.islink(filename)

    def is_parseable (self):
        """
        Check if content is parseable for recursion.

        @return: True if content is parseable
        @rtype: bool
        """
        if self.is_directory():
            return True
        # guess by extension
        for ro in PARSE_EXTENSIONS.values():
            if ro.search(self.url):
                return True
        if firefox_extension.search(self.url):
            return True
        # try to read content (can fail, so catch error)
        try:
            for ro in PARSE_CONTENTS.values():
                if ro.search(self.get_content()[:30]):
                    return True
        except IOError:
            pass
        return False

    def parse_url (self):
        """
        Parse file contents for new links to check.
        """
        if self.is_directory():
            self.parse_html()
            return
        for key, ro in PARSE_EXTENSIONS.items():
            if ro.search(self.url):
                getattr(self, "parse_"+key)()
                return
        if has_sqlite and firefox_extension.search(self.url):
            self.parse_firefox()
            return
        for key, ro in PARSE_CONTENTS.items():
            if ro.search(self.get_content()[:30]):
                getattr(self, "parse_"+key)()
                return

    def parse_firefox (self):
        """Parse a Firefox3 bookmark file."""
        log.debug(LOG_CHECK, "Parsing Firefox bookmarks %s", self)
        conn = sqlite3.connect(self.get_os_filename(), timeout=0.5)
        try:
            c = conn.cursor()
            try:
                sql = """SELECT moz_places.url, moz_places.title
                FROM moz_places WHERE hidden=0"""
                c.execute(sql)
                for url, name in c:
                    url_data = get_url_from(url, self.recursion_level+1,
                        self.aggregate, parent_url=self.url, name=name)
                    self.aggregate.urlqueue.put(url_data)
            finally:
                c.close()
        finally:
            conn.close()

    def get_intern_pattern (self):
        """
        Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        url = absolute_url(self.base_url, self.base_ref, self.parent_url)
        if not url:
            return None
        parts = strformat.url_unicode_split(url)
        path = urlutil.splitparams(parts[2])[0]
        segments = path.split('/')
        if not self.is_directory():
            # cut off filename to have a directory
            segments = segments[:-1]
        path = "/".join(segments)
        return "file://%s" % re.escape(path)
