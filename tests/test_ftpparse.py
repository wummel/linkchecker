# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2010 Bastian Kleineidam
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
Test ftpparse routine.
"""

import unittest
from linkcheck.ftpparse import ftpparse

patterns = (
    # EPLF format
    # http://pobox.com/~djb/proto/eplf.html
    ("+i8388621.29609,m824255902,/,\tdev",
     dict(name='dev', tryretr=False, trycwd=True)),
    ("+i8388621.44468,m839956783,r,s10376,\tRFCEPLF",
     dict(name='RFCEPLF', tryretr=True, trycwd=False)),
    # UNIX-style listing, without inum and without blocks
    ("-rw-r--r--   1 root     other        531 Jan 29 03:26 README",
     dict(name='README', tryretr=True, trycwd=False)),
    ("dr-xr-xr-x   2 root     other        512 Apr  8  1994 etc",
     dict(name='etc', tryretr=False, trycwd=True)),
    ("dr-xr-xr-x   2 root     512 Apr  8  1994 etc",
     dict(name='etc', tryretr=False, trycwd=True)),
    ("lrwxrwxrwx   1 root     other          7 Jan 25 00:17 bin -> usr/bin",
     dict(name='usr/bin', tryretr=True, trycwd=True)),
    # Also produced by Microsoft's FTP servers for Windows:
    ("----------   1 owner    group         1803128 Jul 10 10:18 ls-lR.Z",
     dict(name='ls-lR.Z', tryretr=True, trycwd=False)),
    ("d---------   1 owner    group               0 May  9 19:45 Softlib",
     dict(name='Softlib', tryretr=False, trycwd=True)),
    # Also WFTPD for MSDOS:
    ("-rwxrwxrwx   1 noone    nogroup      322 Aug 19  1996 message.ftp",
     dict(name='message.ftp', tryretr=True, trycwd=False)),
    # Also NetWare:
    ("d [R----F--] supervisor            512       Jan 16 18:53    login",
     dict(name='login', tryretr=False, trycwd=True)),
    ("- [R----F--] rhesus             214059       Oct 20 15:27    cx.exe",
     dict(name='cx.exe', tryretr=True, trycwd=False)),
    # Also NetPresenz for the Mac:
    ("-------r--         326  1391972  1392298 Nov 22  1995 MegaPhone.sit",
     dict(name='MegaPhone.sit', tryretr=True, trycwd=False)),
    ("drwxrwxr-x               folder        2 May 10  1996 network",
     dict(name='network', tryretr=False, trycwd=True)),
    # MultiNet (some spaces removed from examples)
    ("00README.TXT;1      2 30-DEC-1996 17:44 [SYSTEM] (RWED,RWED,RE,RE)",
     dict(name='00README.TXT', tryretr=True, trycwd=False)),
    ("CORE.DIR;1          1  8-SEP-1996 16:09 [SYSTEM] (RWE,RWE,RE,RE)",
     dict(name='CORE', tryretr=False, trycwd=True)),
    # and non-MutliNet VMS:
    ("CII-MANUAL.TEX;1  213/216  29-JAN-1996 03:33:12  [ANONYMOU,ANONYMOUS]   (RWED,RWED,,)",
     dict(name='CII-MANUAL.TEX', tryretr=True, trycwd=False)),
    # MSDOS format
    ("04-27-00  09:09PM       <DIR>          licensed",
     dict(name='licensed', tryretr=False, trycwd=True)),
    ("07-18-00  10:16AM       <DIR>          pub",
     dict(name='pub', tryretr=False, trycwd=True)),
    ("04-14-00  03:47PM                  589 readme.htm",
     dict(name='readme.htm', tryretr=True, trycwd=False)),
    # Some useless lines, safely ignored:
    ("Total of 11 Files, 10966 Blocks.", None), # (VMS)
    ("total 14786", None), # (UNIX)
    ("DISK$ANONFTP:[ANONYMOUS]", None), # (VMS)
    ("Directory DISK$PCSA:[ANONYM]", None), # (VMS)
    ("", None),
)


class TestFtpparse (unittest.TestCase):
    """
    Test FTP LIST line parsing.
    """

    def test_ftpparse (self):
        for line, expected in patterns:
            res = ftpparse(line)
            self.assertEqual(expected, res,
                "got %r\nexpected %r\n%r" % (res, expected, line))
