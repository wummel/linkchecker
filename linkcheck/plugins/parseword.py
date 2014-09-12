# -*- coding: iso-8859-1 -*-
# Copyright (C) 2010-2014 Bastian Kleineidam
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
Parse hyperlinks in Word files.
"""
from . import _ParserPlugin
try:
    import win32com
    import pythoncom
    has_win32com = True
    Error = pythoncom.com_error
except ImportError:
    has_win32com = False
    Error = Exception
from .. import fileutil, log, LOG_PLUGIN


_initialized = False
def init_win32com ():
    """Initialize the win32com.client cache."""
    global _initialized
    if _initialized:
        return
    import win32com.client
    if win32com.client.gencache.is_readonly:
        #allow gencache to create the cached wrapper objects
        win32com.client.gencache.is_readonly = False
        # under py2exe the call in gencache to __init__() does not happen
        # so we use Rebuild() to force the creation of the gen_py folder
        # Note that the python...\win32com.client.gen_py dir must not exist
        # to allow creation of the cache in %temp% for py2exe.
        # This is ensured by excluding win32com.gen_py in setup.py
        win32com.client.gencache.Rebuild()
    _initialized = True


def has_word ():
    """Determine if Word is available on the current system."""
    if not has_win32com:
        return False
    try:
        import _winreg as winreg
    except ImportError:
        import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")
        winreg.CloseKey(key)
        return True
    except (EnvironmentError, ImportError):
        pass
    return False


def constants (name):
    """Helper to return constants. Avoids importing win32com.client in
    other modules."""
    return getattr(win32com.client.constants, name)


def get_word_app ():
    """Return open Word.Application handle, or None if Word is not available
    on this system."""
    if not has_word():
        return None
    # Since this function is called from different threads, initialize
    # the COM layer.
    pythoncom.CoInitialize()
    import win32com.client
    app = win32com.client.gencache.EnsureDispatch("Word.Application")
    app.Visible = False
    return app


def close_word_app (app):
    """Close Word application object."""
    app.Quit()


def open_wordfile (app, filename):
    """Open given Word file with application object."""
    return app.Documents.Open(filename, ReadOnly=True,
      AddToRecentFiles=False, Visible=False, NoEncodingDialog=True)


def close_wordfile (doc):
    """Close word file."""
    doc.Close()


class WordParser(_ParserPlugin):
    """Word parsing plugin."""

    def __init__(self, config):
        """Check for pdfminer."""
        init_win32com()
        if not has_word():
            log.warn(LOG_PLUGIN, "Microsoft Word not found for WordParser plugin")
        super(WordParser, self).__init__(config)

    def applies_to(self, url_data, pagetype=None):
        """Check for Word pagetype."""
        return has_word() and pagetype == 'word'

    def check(self, url_data):
        """Parse Word data."""
        content = url_data.get_content()
        filename = get_temp_filename(content)
        # open word file and parse hyperlinks
        try:
            app = get_word_app()
            try:
                doc = open_wordfile(app, filename)
                if doc is None:
                    raise Error("could not open word file %r" % filename)
                try:
                    for link in doc.Hyperlinks:
                        line = get_line_number(link.Range)
                        name=link.TextToDisplay
                        url_data.add_url(link.Address, name=name, line=line)
                finally:
                    close_wordfile(doc)
            finally:
                close_word_app(app)
        except Error as msg:
            log.warn(LOG_PLUGIN, "Error parsing word file: %s", msg)


def get_line_number(doc, wrange):
    """Get line number for given range object."""
    lineno = 1
    wrange.Select()
    wdFirstCharacterLineNumber = constants("wdFirstCharacterLineNumber")
    wdGoToLine = constants("wdGoToLine")
    wdGoToPrevious = constants("wdGoToPrevious")
    while True:
        curline = doc.Selection.Information(wdFirstCharacterLineNumber)
        doc.Selection.GoTo(wdGoToLine, wdGoToPrevious, Count=1, Name="")
        lineno += 1
        prevline = doc.Selection.Information(wdFirstCharacterLineNumber)
        if prevline == curline:
            break
    return lineno


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

