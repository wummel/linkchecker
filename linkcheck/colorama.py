# These functions are part of the python-colorama module
# They have been adjusted slightly for LinkChecker
#
# Copyright: (C) 2010 Jonathan Hartley <tartley@tartley.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name(s) of the copyright holders nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# from winbase.h
STDOUT = -11
STDERR = -12

from ctypes import (windll, byref, Structure, c_char, c_short, c_uint32,
  c_ushort, ArgumentError, WinError)

handles = {
    STDOUT: windll.kernel32.GetStdHandle(STDOUT),
    STDERR: windll.kernel32.GetStdHandle(STDERR),
}

SHORT = c_short
WORD = c_ushort
DWORD = c_uint32
TCHAR = c_char

class COORD(Structure):
    """struct in wincon.h"""
    _fields_ = [
        ('X', SHORT),
        ('Y', SHORT),
    ]

class  SMALL_RECT(Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("Left", SHORT),
        ("Top", SHORT),
        ("Right", SHORT),
        ("Bottom", SHORT),
    ]

class CONSOLE_SCREEN_BUFFER_INFO(Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]
    def __str__(self):
        """Get string representation of console screen buffer info."""
        return '(%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)' % (
            self.dwSize.Y, self.dwSize.X
            , self.dwCursorPosition.Y, self.dwCursorPosition.X
            , self.wAttributes
            , self.srWindow.Top, self.srWindow.Left, self.srWindow.Bottom, self.srWindow.Right
            , self.dwMaximumWindowSize.Y, self.dwMaximumWindowSize.X
        )

def GetConsoleScreenBufferInfo(stream_id=STDOUT):
    """Get console screen buffer info object."""
    handle = handles[stream_id]
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    success = windll.kernel32.GetConsoleScreenBufferInfo(
        handle, byref(csbi))
    if not success:
        raise WinError()
    return csbi


def SetConsoleTextAttribute(stream_id, attrs):
    """Set a console text attribute."""
    handle = handles[stream_id]
    return windll.kernel32.SetConsoleTextAttribute(handle, attrs)


# from wincon.h
BLACK   = 0
BLUE    = 1
GREEN   = 2
CYAN    = 3
RED     = 4
MAGENTA = 5
YELLOW  = 6
GREY    = 7

# from wincon.h
NORMAL = 0x00 # dim text, dim background
BRIGHT = 0x08 # bright text, dim background

_default_foreground = None
_default_background = None
_default_style = None


def init():
    """Initialize foreground and background attributes."""
    global _default_foreground, _default_background, _default_style
    try:
        attrs = GetConsoleScreenBufferInfo().wAttributes
    except (ArgumentError, WindowsError):
        _default_foreground = GREY
        _default_background = BLACK
        _default_style = NORMAL
    else:
        _default_foreground = attrs & 7
        _default_background = (attrs >> 4) & 7
        _default_style = attrs & BRIGHT


def get_attrs(foreground, background, style):
    """Get foreground and background attributes."""
    return foreground + (background << 4) + style


def set_console(stream=STDOUT, foreground=None, background=None, style=None):
    """Set console foreground and background attributes."""
    if foreground is None:
        foreground = _default_foreground
    if background is None:
        background = _default_background
    if style is None:
        style = _default_style
    attrs = get_attrs(foreground, background, style)
    SetConsoleTextAttribute(stream, attrs)


def reset_console(stream=STDOUT):
    """Reset the console."""
    set_console(stream=stream)


def get_console_size():
    """Get the console size."""
    return GetConsoleScreenBufferInfo().dwSize
