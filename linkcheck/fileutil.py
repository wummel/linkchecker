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
import locale
import stat
import fnmatch
import tempfile
import importlib
from distutils.spawn import find_executable

from .decorators import memoized

def write_file (filename, content, backup=False, callback=None):
    """Overwrite a possibly existing file with new content. Do this
    in a manner that does not leave truncated or broken files behind.
    @param filename: name of file to write
    @type filename: string
    @param content: file content to write
    @type content: string
    @param backup: if backup file should be left
    @type backup: bool
    @param callback: non-default storage function
    @type callback: None or function taking two parameters (fileobj, content)
    """
    # first write in a temp file
    f = file(filename+".tmp", 'wb')
    if callback is None:
        f.write(content)
    else:
        callback(f, content)
    f.close()
    # move orig file to backup
    if os.path.exists(filename):
        os.rename(filename, filename+".bak")
    # move temp file to orig
    os.rename(filename+".tmp", filename)
    # remove backup
    if not backup and os.path.exists(filename+".bak"):
        os.remove(filename+".bak")


def has_module (name, without_error=True):
    """Test if given module can be imported.
    @param without_error: True if module must not throw any errors when importing
    @return: flag if import is successful
    @rtype: bool
    """
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False
    except Exception:
        # some modules raise errors when intitializing
        return not without_error


class GlobDirectoryWalker (object):
    """A forward iterator that traverses a directory tree."""

    def __init__ (self, directory, pattern="*"):
        """Set start directory and pattern matcher."""
        self.stack = [directory]
        self.pattern = pattern
        self.files = []
        self.index = 0

    def __getitem__ (self, index):
        """Search for next filename."""
        while True:
            try:
                filename = self.files[self.index]
                self.index += 1
            except IndexError:
                # Pop next directory from stack. This effectively
                # stops the iteration if stack is empty.
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
                self.index = 0
            else:
                # got a filename
                fullname = os.path.join(self.directory, filename)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    self.stack.append(fullname)
                if fnmatch.fnmatch(filename, self.pattern):
                    return fullname

# alias
rglob = GlobDirectoryWalker


class Buffer (object):
    """Holds buffered data"""

    def __init__ (self, empty=''):
        """Initialize buffer."""
        self.empty = self.buf = empty
        self.tmpbuf = []
        self.pos = 0

    def __len__ (self):
        """Buffer length."""
        return self.pos

    def write (self, data):
        """Write data to buffer."""
        self.tmpbuf.append(data)
        self.pos += len(data)

    def flush (self, overlap=0):
        """Flush buffered data and return it."""
        self.buf += self.empty.join(self.tmpbuf)
        self.tmpbuf = []
        if overlap and overlap < self.pos:
            data = self.buf[:-overlap]
            self.buf = self.buf[-overlap:]
        else:
            data = self.buf
            self.buf = self.empty
        return data


def get_mtime (filename):
    """Return modification time of filename or zero on errors."""
    try:
        return os.path.getmtime(filename)
    except os.error:
        return 0


def get_size (filename):
    """Return file size in Bytes, or -1 on error."""
    try:
        return os.path.getsize(filename)
    except os.error:
        return -1


# http://developer.gnome.org/doc/API/2.0/glib/glib-running.html
if "G_FILENAME_ENCODING" in os.environ:
    FSCODING = os.environ["G_FILENAME_ENCODING"].split(",")[0]
    if FSCODING == "@locale":
        FSCODING = locale.getpreferredencoding()
elif "G_BROKEN_FILENAMES" in os.environ:
    FSCODING = locale.getpreferredencoding()
else:
    FSCODING = "utf-8"

def pathencode (path):
    """Encode a path string with the platform file system encoding."""
    if isinstance(path, unicode) and not os.path.supports_unicode_filenames:
        path = path.encode(FSCODING, "replace")
    return path


# cache for modified check {absolute filename -> mtime}
_mtime_cache = {}
def has_changed (filename):
    """Check if filename has changed since the last check. If this
    is the first check, assume the file is changed."""
    key = os.path.abspath(filename)
    mtime = get_mtime(key)
    if key not in _mtime_cache:
        _mtime_cache[key] = mtime
        return True
    return mtime > _mtime_cache[key]


def get_temp_file (mode='r', **kwargs):
    """Return tuple (open file object, filename) pointing to a temporary
    file."""
    fd, filename = tempfile.mkstemp(**kwargs)
    return os.fdopen(fd, mode), filename


def is_tty (fp):
    """Check if is a file object pointing to a TTY."""
    return (hasattr(fp, "isatty") and fp.isatty())


@memoized
def is_readable(filename):
    """Check if file is a regular file and is readable."""
    return os.path.isfile(filename) and os.access(filename, os.R_OK)


def is_accessable_by_others(filename):
    """Check if file is group or world accessable."""
    mode = os.stat(filename)[stat.ST_MODE]
    return mode & (stat.S_IRWXG | stat.S_IRWXO)


def is_writable_by_others(filename):
    """Check if file or directory is world writable."""
    mode = os.stat(filename)[stat.ST_MODE]
    return mode & stat.S_IWOTH


@memoized
def is_writable(filename):
    """Check if
    - the file is a regular file and is writable, or
    - the file does not exist and its parent directory exists and is
      writable
    """
    if not os.path.exists(filename):
        parentdir = os.path.dirname(filename)
        return os.path.isdir(parentdir) and os.access(parentdir, os.W_OK)
    return os.path.isfile(filename) and os.access(filename, os.W_OK)
