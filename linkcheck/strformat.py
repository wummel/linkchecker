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
#
# Some functions have been taken and adjusted from the quodlibet
# source. Quodlibet is (C) 2004-2005 Joe Wreschnig, Michael Urman
# and licensed under the GNU General Public License version 2.
"""
Various string utility functions. Note that these functions are not
necessarily optimised for large strings, so use with care.
"""
# some handy time constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR

import re
import textwrap
import codecs
import os
import math
import time
try:
    import urlparse
except ImportError:
    # Python 3
    from urllib import parse as urlparse
import locale
import pydoc
from . import i18n


def unicode_safe (s, encoding=i18n.default_encoding, errors='replace'):
    """Get unicode string without raising encoding errors. Unknown
    characters of the given encoding will be ignored.

    @param s: the string to be decoded
    @type s: any object except None
    @return: if s is already unicode, return s unchanged; else return
        decoded unicode string of str(s)
    @rtype: unicode
    """
    assert s is not None, "argument to unicode_safe was None"
    if isinstance(s, unicode):
        # s is already unicode, nothing to do
        return s
    return unicode(str(s), encoding, errors)


def ascii_safe (s):
    """Get ASCII string without raising encoding errors. Unknown
    characters of the given encoding will be ignored.

    @param s: the Unicode string to be encoded
    @type s: unicode or None
    @return: encoded ASCII version of s, or None if s was None
    @rtype: string
    """
    if isinstance(s, unicode):
        s = s.encode('ascii', 'ignore')
    return s


def is_ascii (s):
    """Test if a string can be encoded in ASCII."""
    try:
        s.encode('ascii', 'strict')
        return True
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False


def is_encoding (text):
    """Check if string is a valid encoding."""
    try:
        return codecs.lookup(text)
    except (LookupError, ValueError):
        return False


def url_unicode_split (url):
    """Like urlparse.urlsplit(), but always returning unicode parts."""
    return [unicode_safe(s) for s in urlparse.urlsplit(url)]


def unquote (s, matching=False):
    """Remove leading and ending single and double quotes.
    The quotes need to match if matching is True. Only one quote from each
    end will be stripped.

    @return: if s evaluates to False, return s as is, else return
        string with stripped quotes
    @rtype: unquoted string, or s unchanged if it is evaluting to False
    """
    if not s:
        return s
    if len(s) < 2:
        return s
    if matching:
        if s[0] in ("\"'") and s[0] == s[-1]:
            s = s[1:-1]
    else:
        if s[0] in ("\"'"):
            s = s[1:]
        if s[-1] in ("\"'"):
            s = s[:-1]
    return s


_para_mac = r"(?:%(sep)s)(?:(?:%(sep)s)\s*)+" % {'sep': '\r'}
_para_posix = r"(?:%(sep)s)(?:(?:%(sep)s)\s*)+" % {'sep': '\n'}
_para_win = r"(?:%(sep)s)(?:(?:%(sep)s)\s*)+" % {'sep': '\r\n'}
_para_ro = re.compile("%s|%s|%s" % (_para_mac, _para_posix, _para_win))

def get_paragraphs (text):
    """A new paragraph is considered to start at a line which follows
    one or more blank lines (lines containing nothing or just spaces).
    The first line of the text also starts a paragraph."""
    if not text:
        return []
    return _para_ro.split(text)


def wrap (text, width, **kwargs):
    """Adjust lines of text to be not longer than width. The text will be
    returned unmodified if width <= 0.
    See textwrap.wrap() for a list of supported kwargs.
    Returns text with lines no longer than given width."""
    if width <= 0 or not text:
        return text
    ret = []
    for para in get_paragraphs(text):
        text = " ".join(para.strip().split())
        ret.extend(textwrap.wrap(text, width, **kwargs))
    return os.linesep.join(ret)


def indent (text, indent_string="  "):
    """Indent each line of text with the given indent string."""
    lines = str(text).splitlines()
    return os.linesep.join("%s%s" % (indent_string, x) for x in lines)


def get_line_number (s, index):
    r"""Return the line number of s[index] or zero on errors.
    Lines are assumed to be separated by the ASCII character '\n'."""
    i = 0
    if index < 0:
        return 0
    line = 1
    while i < index:
        if s[i] == '\n':
            line += 1
        i += 1
    return line


def paginate (text):
    """Print text in pages of lines."""
    pydoc.pager(text)


_markup_re = re.compile("<.*?>", re.DOTALL)

def remove_markup (s):
    """Remove all <*> html markup tags from s."""
    mo = _markup_re.search(s)
    while mo:
        s = s[0:mo.start()] + s[mo.end():]
        mo = _markup_re.search(s)
    return s


def strsize (b, grouping=True):
    """Return human representation of bytes b. A negative number of bytes
    raises a value error."""
    if b < 0:
        raise ValueError("Invalid negative byte number")
    if b < 1024:
        return u"%sB" % locale.format("%d", b, grouping)
    if b < 1024 * 10:
        return u"%sKB" % locale.format("%d", (b // 1024), grouping)
    if b < 1024 * 1024:
        return u"%sKB" % locale.format("%.2f", (float(b) / 1024), grouping)
    if b < 1024 * 1024 * 10:
        return u"%sMB" % locale.format("%.2f", (float(b) / (1024*1024)), grouping)
    if b < 1024 * 1024 * 1024:
        return u"%sMB" % locale.format("%.1f", (float(b) / (1024*1024)), grouping)
    if b < 1024 * 1024 * 1024 * 10:
        return u"%sGB" % locale.format("%.2f", (float(b) / (1024*1024*1024)), grouping)
    return u"%sGB" % locale.format("%.1f", (float(b) / (1024*1024*1024)), grouping)


def strtime (t, func=time.localtime):
    """Return ISO 8601 formatted time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", func(t)) + strtimezone()


# from quodlibet
def strduration (duration):
    """Turn a time value in seconds into hh:mm:ss or mm:ss."""
    if duration < 0:
        duration = abs(duration)
        prefix = "-"
    else:
        prefix = ""
    duration = math.ceil(duration)
    if duration >= SECONDS_PER_HOUR: # 1 hour
        # time, in hours:minutes:seconds
        return "%s%02d:%02d:%02d" % (prefix, duration // SECONDS_PER_HOUR,
                                   (duration % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE,
                                    duration % SECONDS_PER_MINUTE)
    else:
        # time, in minutes:seconds
        return "%s%02d:%02d" % (prefix, duration // SECONDS_PER_MINUTE,
                                 duration % SECONDS_PER_MINUTE)


# from quodlibet
def strduration_long (duration, do_translate=True):
    """Turn a time value in seconds into x hours, x minutes, etc."""
    if do_translate:
        # use global translator functions
        global _, _n
    else:
        # do not translate
        _ = lambda x: x
        _n = lambda a, b, n: a if n==1 else b
    if duration < 0:
        duration = abs(duration)
        prefix = "-"
    else:
        prefix = ""
    if duration < 1:
        return _("%(prefix)s%(duration).02f seconds") % \
               {"prefix": prefix, "duration": duration}
    # translation dummies
    _n("%d second", "%d seconds", 1)
    _n("%d minute", "%d minutes", 1)
    _n("%d hour", "%d hours", 1)
    _n("%d day", "%d days", 1)
    _n("%d year", "%d years", 1)
    cutoffs = [
        (60, "%d second", "%d seconds"),
        (60, "%d minute", "%d minutes"),
        (24, "%d hour", "%d hours"),
        (365, "%d day", "%d days"),
        (None, "%d year", "%d years"),
    ]
    time_str = []
    for divisor, single, plural in cutoffs:
        if duration < 1:
            break
        if divisor is None:
            duration, unit = 0, duration
        else:
            duration, unit = divmod(duration, divisor)
        if unit:
            time_str.append(_n(single, plural, unit) % unit)
    time_str.reverse()
    if len(time_str) > 2:
        time_str.pop()
    return "%s%s" % (prefix, ", ".join(time_str))


def strtimezone ():
    """Return timezone info, %z on some platforms, but not supported on all.
    """
    if time.daylight:
        zone = time.altzone
    else:
        zone = time.timezone
    return "%+04d" % (-zone//SECONDS_PER_HOUR)


def stripurl(s):
    """Remove any lines from string after the first line.
    Also remove whitespace at start and end from given string."""
    if not s:
        return s
    return s.splitlines()[0].strip()


def limit (s, length=72):
    """If the length of the string exceeds the given limit, it will be cut
    off and three dots will be appended.

    @param s: the string to limit
    @type s: string
    @param length: maximum length
    @type length: non-negative integer
    @return: limited string, at most length+3 characters long
    """
    assert length >= 0, "length limit must be a non-negative integer"
    if not s or len(s) <= length:
        return s
    if length == 0:
        return ""
    return "%s..." % s[:length]


def strline (s):
    """Display string representation on one line."""
    return strip_control_chars(u"`%s'" % unicode(s).replace(u"\n", u"\\n"))


def format_feature_warning (**kwargs):
    """Format warning that a module could not be imported and that it should
    be installed for a certain URL.
    """
    return _("Could not import %(module)s for %(feature)s. Install %(module)s from %(url)s to use this feature.") % kwargs


def strip_control_chars(text):
    """Remove console control characters from text."""
    if text:
        return re.sub(r"[\x01-\x1F\x7F]", "", text)
    return text
