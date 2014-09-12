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
Handle local file: links.
"""

import re
import os
try:
    import urlparse
except ImportError:
    # Python 3
    from urllib import parse as urlparse
import urllib
try:
    from urllib2 import urlopen
except ImportError:
    # Python 3
    from urllib.request import urlopen
from datetime import datetime

from . import urlbase, get_index_html
from .. import log, LOG_CHECK, fileutil, mimeutil, LinkCheckerError, url as urlutil
from ..bookmarks import firefox
from .const import WARN_FILE_MISSING_SLASH, WARN_FILE_SYSTEM_PATH


def get_files (dirname):
    """Get iterator of entries in directory. Only allows regular files
    and directories, no symlinks."""
    for entry in os.listdir(dirname):
        fullentry = os.path.join(dirname, entry)
        if os.path.islink(fullentry):
            continue
        if os.path.isfile(fullentry):
            yield entry
        elif os.path.isdir(fullentry):
            yield entry+"/"


def prepare_urlpath_for_nt (path):
    """
    URLs like 'file://server/path/' result in a path named '/server/path'.
    However urllib.url2pathname expects '////server/path'.
    """
    if '|' not in path:
        return "////"+path.lstrip("/")
    return path


def get_nt_filename (path):
    """Return case sensitive filename for NT path."""
    unc, rest = os.path.splitunc(path)
    head, tail = os.path.split(rest)
    if not tail:
        return path
    for fname in os.listdir(unc+head):
        if fname.lower() == tail.lower():
            return os.path.join(get_nt_filename(unc+head), fname)
    log.error(LOG_CHECK, "could not find %r in %r", tail, head)
    return path


def get_os_filename (path):
    """Return filesystem path for given URL path."""
    if os.name == 'nt':
        path = prepare_urlpath_for_nt(path)
    res = urllib.url2pathname(fileutil.pathencode(path))
    if os.name == 'nt' and res.endswith(':') and len(res) == 2:
        # Work around http://bugs.python.org/issue11474
        res += os.sep
    return res


def is_absolute_path (path):
    """Check if given path is absolute. On Windows absolute paths start
    with a drive letter. On all other systems absolute paths start with
    a slash."""
    if os.name == 'nt':
        if re.search(r"^[a-zA-Z]:", path):
            return True
        path = path.replace("\\", "/")
    return path.startswith("/")


class FileUrl (urlbase.UrlBase):
    """
    Url link with file scheme.
    """

    def init (self, base_ref, base_url, parent_url, recursion_level,
              aggregate, line, column, page, name, url_encoding, extern):
        """Initialize the scheme."""
        super(FileUrl, self).init(base_ref, base_url, parent_url,
         recursion_level, aggregate, line, column, page, name, url_encoding, extern)
        self.scheme = u'file'

    def build_base_url(self):
        """The URL is normed according to the platform:
         - the base URL is made an absolute file:// URL
         - under Windows platform the drive specifier is normed
        """
        if self.base_url is None:
            return
        base_url = self.base_url
        if not (self.parent_url or self.base_ref or base_url.startswith("file:")):
            base_url = os.path.expanduser(base_url)
            if not is_absolute_path(base_url):
                try:
                    base_url = os.getcwd()+"/"+base_url
                except OSError as msg:
                    # occurs on stale remote filesystems (eg. NFS)
                    errmsg = _("Could not get current working directory: %(msg)s") % dict(msg=msg)
                    raise LinkCheckerError(errmsg)
                if os.path.isdir(base_url):
                    base_url += "/"
            base_url = "file://"+base_url
        if os.name == "nt":
            base_url = base_url.replace("\\", "/")
            # transform c:/windows into /c|/windows
            base_url = re.sub("^file://(/?)([a-zA-Z]):", r"file:///\2|", base_url)
            # transform file://path into file:///path
            base_url = re.sub("^file://([^/])", r"file:///\1", base_url)
        self.base_url = unicode(base_url)

    def build_url (self):
        """
        Calls super.build_url() and adds a trailing slash to directories.
        """
        self.build_base_url()
        if self.parent_url is not None:
            # URL joining with the parent URL only works if the query
            # of the base URL are removed first.
            # Otherwise the join function thinks the query is part of
            # the file name.
            from .urlbase import url_norm
            # norm base url - can raise UnicodeError from url.idna_encode()
            base_url, is_idn = url_norm(self.base_url, self.encoding)
            urlparts = list(urlparse.urlsplit(base_url))
            # ignore query part for filesystem urls
            urlparts[3] = ''
            self.base_url = urlutil.urlunsplit(urlparts)
        super(FileUrl, self).build_url()
        # ignore query and fragment url parts for filesystem urls
        self.urlparts[3] = self.urlparts[4] = ''
        if self.is_directory() and not self.urlparts[2].endswith('/'):
            self.add_warning(_("Added trailing slash to directory."),
                           tag=WARN_FILE_MISSING_SLASH)
            self.urlparts[2] += '/'
        self.url = urlutil.urlunsplit(self.urlparts)

    def add_size_info (self):
        """Get size of file content and modification time from filename path."""
        if self.is_directory():
            # Directory size always differs from the customer index.html
            # that is generated. So return without calculating any size.
            return
        filename = self.get_os_filename()
        self.size = fileutil.get_size(filename)
        self.modified = datetime.utcfromtimestamp(fileutil.get_mtime(filename))

    def check_connection (self):
        """
        Try to open the local file. Under NT systems the case sensitivity
        is checked.
        """
        if (self.parent_url is not None and
           not self.parent_url.startswith(u"file:")):
            msg = _("local files are only checked without parent URL or when the parent URL is also a file")
            raise LinkCheckerError(msg)
        if self.is_directory():
            self.set_result(_("directory"))
        else:
            url = fileutil.pathencode(self.url)
            self.url_connection = urlopen(url)
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

    def read_content (self):
        """Return file content, or in case of directories a dummy HTML file
        with links to the files."""
        if self.is_directory():
            data = get_index_html(get_files(self.get_os_filename()))
            if isinstance(data, unicode):
                data = data.encode("iso8859-1", "ignore")
        else:
            data = super(FileUrl, self).read_content()
        return data

    def get_os_filename (self):
        """
        Construct os specific file path out of the file:// URL.

        @return: file name
        @rtype: string
        """
        return get_os_filename(self.urlparts[2])

    def get_temp_filename (self):
        """Get filename for content to parse."""
        return self.get_os_filename()

    def is_directory (self):
        """
        Check if file is a directory.

        @return: True iff file is a directory
        @rtype: bool
        """
        filename = self.get_os_filename()
        return os.path.isdir(filename) and not os.path.islink(filename)

    def is_parseable (self):
        """Check if content is parseable for recursion.

        @return: True if content is parseable
        @rtype: bool
        """
        if self.is_directory():
            return True
        if firefox.has_sqlite and firefox.extension.search(self.url):
            return True
        if self.content_type in self.ContentMimetypes:
            return True
        log.debug(LOG_CHECK, "File with content type %r is not parseable.", self.content_type)
        return False

    def set_content_type (self):
        """Return URL content type, or an empty string if content
        type could not be found."""
        if self.url:
            self.content_type = mimeutil.guess_mimetype(self.url, read=self.get_content)
        else:
            self.content_type = u""

    def get_intern_pattern (self, url=None):
        """Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        if url is None:
            url = self.url
        if not url:
            return None
        if url.startswith('file://'):
            i = url.rindex('/')
            if i > 6:
                # remove last filename to make directory internal
                url = url[:i+1]
        return re.escape(url)

    def add_url (self, url, line=0, column=0, page=0, name=u"", base=None):
        """If a local webroot directory is configured, replace absolute URLs
        with it. After that queue the URL data for checking."""
        webroot = self.aggregate.config["localwebroot"]
        if webroot and url and url.startswith(u"/"):
            url = webroot + url[1:]
            log.debug(LOG_CHECK, "Applied local webroot `%s' to `%s'.", webroot, url)
        super(FileUrl, self).add_url(url, line=line, column=column, page=page, name=name, base=base)
