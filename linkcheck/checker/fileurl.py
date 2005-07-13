# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
import os.path
import time
import urlparse
import urllib

import urlbase
import linkcheck
import linkcheck.log
import linkcheck.checker

# if file extension lookup was unsuccessful, look at the content
contents = {
    "html": re.compile(r'^(?i)<(!DOCTYPE html|html|head|title)'),
    "opera" : re.compile(r'^Opera Hotlist'),
    "text" : re.compile(r'(?i)^# LinkChecker URL list'),
}


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
    linkcheck.log.error(linkcheck.LOG_CHECK, "could not find %r in %r",
                        tail, head)
    return path


class FileUrl (urlbase.UrlBase):
    """
    Url link with file scheme.
    """

    def init (self, base_ref, base_url, parent_url, recursion_level,
              consumer, line, column, name):
        """
        Besides the usual initialization the URL is normed according
        to the platform:
         - the base URL is made an absolute file:// URL
         - under Windows platform the drive specifier is normed
        """
        super(FileUrl, self).init(base_ref, base_url, parent_url,
                               recursion_level, consumer, line, column, name)
        if self.base_url is None:
            return
        base_url = self.base_url
        if not (parent_url or base_ref or base_url.startswith("file:")):
            base_url = os.path.expanduser(base_url)
            if not base_url.startswith("/"):
                base_url = os.getcwd()+"/"+base_url
            base_url = "file://"+base_url
        base_url = base_url.replace("\\", "/")
        # transform c:/windows into /c|/windows
        base_url = re.sub("^file://(/?)([a-zA-Z]):", r"file:///\2|", base_url)
        # norm base url again after changing
        if self.base_url != base_url:
            self.base_url, is_idn = linkcheck.url.url_norm(base_url)

    def build_url (self):
        """
        Calls super.build_url() and adds a trailing slash to directories.
        """
        super(FileUrl, self).build_url()
        # ignore query and fragment url parts for filesystem urls
        self.urlparts[3] = self.urlparts[4] = ''
        if self.is_directory() and not self.urlparts[2].endswith('/'):
            self.add_warning(_("Added trailing slash to directory."),
                           tag="file-missing-slash")
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
            super(FileUrl, self).check_connection()
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
            self.add_warning(_("The URL path %r is not the same as the " \
                               "system path %r. You should always use " \
                               "the system path in URLs.") % (path, realpath),
                               tag="file-system-path")
        pass

    def get_content (self):
        """
        Return file content, or in case of directories a dummy HTML file
        with links to the files.
        """
        if not self.valid:
            return ""
        if self.has_content:
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
        data = linkcheck.checker.get_index_html(files)
        self.data = data.encode("iso8859-1", "ignore")
        self.dltime = time.time() - t
        self.dlsize = len(self.data)
        self.has_content = True
        return self.data

    def is_html (self):
        """
        Check if file is a parseable HTML file.
        """
        if linkcheck.checker.extensions['html'].search(self.url):
            return True
        if contents['html'].search(self.get_content()):
            return True
        return False

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
        return urllib.url2pathname(path)

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
        for ro in linkcheck.checker.extensions.values():
            if ro.search(self.url):
                return True
        # try to read content (can fail, so catch error)
        try:
            for ro in contents.values():
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
        for key, ro in linkcheck.checker.extensions.items():
            if ro.search(self.url):
                getattr(self, "parse_"+key)()
                return
        for key, ro in contents.items():
            if ro.search(self.get_content()[:30]):
                getattr(self, "parse_"+key)()
                return

    def get_intern_pattern (self):
        """
        Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        absolute = linkcheck.checker.absolute_url
        url = absolute(self.base_url, self.base_ref, self.parent_url)
        if not url:
            return None
        parts = linkcheck.strformat.url_unicode_split(url)
        path, params = linkcheck.url.splitparams(parts[2])
        segments = path.split('/')
        if not self.is_directory():
            # cut off filename to have a directory
            segments = segments[:-1]
        path = "/".join(segments)
        return "file://%s" % re.escape(path)

