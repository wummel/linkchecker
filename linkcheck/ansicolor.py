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
ANSI Color definitions and functions. For Windows systems, the colorama module
uses ctypes and Windows DLLs to generate colored output.

From Term::ANSIColor, applies also to this module:

The codes output by this module are standard terminal control codes,
complying with ECMA-48 and ISO 6429 (generally referred to as ``ANSI color''
for the color codes). The non-color control codes (bold, dark, italic,
underline, and reverse) are part of the earlier ANSI X3.64 standard for
control sequences for video terminals and peripherals.

Note that not all displays are ISO 6429-compliant, or even X3.64-compliant
(or are even attempting to be so).

Jean Delvare provided the following table of different common terminal
emulators and their support for the various attributes and others have
helped me flesh it out::

              clear    bold     dark    under    blink   reverse  conceal
 ------------------------------------------------------------------------
 xterm         yes      yes      no      yes     bold      yes      yes
 linux         yes      yes      yes    bold      yes      yes      no
 rxvt          yes      yes      no      yes  bold/black   yes      no
 dtterm        yes      yes      yes     yes    reverse    yes      yes
 teraterm      yes    reverse    no      yes    rev/red    yes      no
 aixterm      kinda   normal     no      yes      no       yes      yes
 PuTTY         yes     color     no      yes      no       yes      no
 Windows       yes      no       no      no       no       yes      no
 Cygwin SSH    yes      yes      no     color    color    color     yes

SEE ALSO

ECMA-048 is available on-line (at least at the time of this writing) at
http://www.ecma-international.org/publications/standards/ECMA-048.HTM.

ISO 6429 is available from ISO for a charge; the author of this module does
not own a copy of it. Since the source material for ISO 6429 was ECMA-048
and the latter is available for free, there seems little reason to obtain
the ISO standard.
"""

import os
import logging
import types
from .fileutil import has_module, is_tty
if os.name == 'nt':
    from . import colorama

has_curses = has_module("curses")

# Color constants

# Escape for ANSI colors
AnsiEsc = "\x1b[%sm"

# Control constants
bold = 'bold'
light = 'light'
underline = 'underline'
blink = 'blink'
invert = 'invert'
concealed = 'concealed'

# Control numbers
AnsiControl = {
    None:      '',
    bold:      '1',
    light:     '2',
    #italic:   '3', # unsupported
    underline: '4',
    blink:     '5',
    #rapidblink: '6', # unsupported
    invert:    '7',
    concealed: '8',
    #strikethrough: '9', # unsupported
}

# Color constants
default = 'default'
black = 'black'
red = 'red'
green = 'green'
yellow = 'yellow'
blue = 'blue'
purple = 'purple'
cyan = 'cyan'
white = 'white'

# inverse colors
Black = 'Black'
Red = 'Red'
Green = 'Green'
Yellow = 'Yellow'
Blue = 'Blue'
Purple = 'Purple'
Cyan = 'Cyna'
White = 'White'

InverseColors = (Black, Red, Green, Yellow, Blue, Purple, Cyan, White)

# Ansi color numbers; capitalized colors are inverse
AnsiColor = {
    None:    '0',
    default: '0',
    black:   '30',
    red:     '31',
    green:   '32',
    yellow:  '33',
    blue:    '34',
    purple:  '35',
    cyan:    '36',
    white:   '37',
    Black:   '40',
    Red:     '41',
    Green:   '42',
    Yellow:  '43',
    Blue:    '44',
    Purple:  '45',
    Cyan:    '46',
    White:   '47',
}

if os.name == 'nt':
    # Windows color numbers; capitalized colors are used as background
    WinColor = {
        None:    None,
        default: colorama.GREY,
        black:   colorama.BLACK,
        red:     colorama.RED,
        green:   colorama.GREEN,
        yellow:  colorama.YELLOW,
        blue:    colorama.BLUE,
        purple:  colorama.MAGENTA,
        cyan:    colorama.CYAN,
        white:   colorama.GREY,
        Black:   colorama.BLACK,
        Red:     colorama.RED,
        Green:   colorama.GREEN,
        Yellow:  colorama.YELLOW,
        Blue:    colorama.BLUE,
        Purple:  colorama.MAGENTA,
        Cyan:    colorama.CYAN,
        White:   colorama.GREY,
    }

# pc speaker beep escape code
Beep = "\007"


def esc_ansicolor (color):
    """convert a named color definition to an escaped ANSI color"""
    control = ''
    if ";" in color:
        control, color = color.split(";", 1)
        control = AnsiControl.get(control, '')+";"
    cnum = AnsiColor.get(color, '0')
    return AnsiEsc % (control+cnum)

AnsiReset = esc_ansicolor(default)


def get_win_color(color):
    """Convert a named color definition to Windows console color foreground,
    background and style numbers."""
    foreground = background = style = None
    control = ''
    if ";" in color:
        control, color = color.split(";", 1)
        if control == bold:
            style = colorama.BRIGHT
    if color in InverseColors:
        background = WinColor[color]
    else:
        foreground = WinColor.get(color)
    return foreground, background, style


def has_colors (fp):
    """Test if given file is an ANSI color enabled tty."""
    # The is_tty() function ensures that we do not colorize
    # redirected streams, as this is almost never what we want
    if not is_tty(fp):
        return False
    if os.name == 'nt':
        return True
    elif has_curses:
        import curses
        try:
            curses.setupterm(os.environ.get("TERM"), fp.fileno())
            # More than 8 colors are good enough.
            return curses.tigetnum("colors") >= 8
        except curses.error:
            return False
    return False


def get_columns (fp):
    """Return number of columns for given file."""
    if not is_tty(fp):
        return 80
    if os.name == 'nt':
        return colorama.get_console_size().X
    if has_curses:
        import curses
        try:
            curses.setupterm(os.environ.get("TERM"), fp.fileno())
            return curses.tigetnum("cols")
        except curses.error:
           pass
    return 80


def _write_color_colorama (fp, text, color):
    """Colorize text with given color."""
    foreground, background, style = get_win_color(color)
    colorama.set_console(foreground=foreground, background=background,
      style=style)
    fp.write(text)
    colorama.reset_console()


def _write_color_ansi (fp, text, color):
    """Colorize text with given color."""
    fp.write(esc_ansicolor(color))
    fp.write(text)
    fp.write(AnsiReset)


if os.name == 'nt':
    write_color = _write_color_colorama
    colorama.init()
else:
    write_color = _write_color_ansi


class Colorizer (object):
    """Prints colored messages to streams."""

    def __init__ (self, fp):
        """Initialize with given stream (file-like object)."""
        super(Colorizer, self).__init__()
        self.fp = fp
        if has_colors(fp):
            self.write = self._write_color
        else:
            self.write = self._write

    def _write (self, text, color=None):
        """Print text as-is."""
        self.fp.write(text)

    def _write_color (self, text, color=None):
        """Print text with given color. If color is None, print text as-is."""
        if color is None:
            self.fp.write(text)
        else:
            write_color(self.fp, text, color)

    def __getattr__ (self, name):
        """Delegate attribute access to the stored stream object."""
        return getattr(self.fp, name)


class ColoredStreamHandler (logging.StreamHandler, object):
    """Send colored log messages to streams (file-like objects)."""

    def __init__ (self, strm=None):
        """Log to given stream (a file-like object) or to stderr if
        strm is None.
        """
        super(ColoredStreamHandler, self).__init__(strm)
        self.stream = Colorizer(self.stream)
        # standard log level colors (used by get_color)
        self.colors = {
            logging.WARN: 'bold;yellow',
            logging.ERROR: 'light;red',
            logging.CRITICAL: 'bold;red',
            logging.DEBUG: 'white',
        }

    def get_color (self, record):
        """Get appropriate color according to log level.
        """
        return self.colors.get(record.levelno, 'default')

    def emit (self, record):
        """Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline
        [N.B. this may be removed depending on feedback].
        """
        color = self.get_color(record)
        msg = self.format(record)
        if not hasattr(types, "UnicodeType"):
            # no unicode support
            self.stream.write("%s" % msg, color=color)
        else:
            try:
                self.stream.write("%s" % msg, color=color)
            except UnicodeError:
                self.stream.write("%s" % msg.encode("UTF-8"),
                                  color=color)
        self.stream.write(os.linesep)
        self.flush()
