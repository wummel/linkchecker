# -*- coding: iso-8859-1 -*-
# Copyright (C) 2009-2014 Bastian Kleineidam
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
Python implementation of a part of Dan Bernstein's ftpparse library.

See also http://cr.yp.to/ftpparse.html
"""

months = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
          "oct", "nov", "dec")
def ismonth (txt):
    """Check if given text is a month name."""
    return txt.lower() in months


def ftpparse (line):
    """Parse a FTP list line into a dictionary with attributes:
    name - name of file (string)
    trycwd - False if cwd is definitely pointless, True otherwise
    tryretr - False if retr is definitely pointless, True otherwise

    If the line has no file information, None is returned
    """
    if len(line) < 2:
        # an empty name in EPLF, with no info, could be 2 chars
        return None
    info = dict(name=None, trycwd=False, tryretr=False)

    # EPLF format
    # http://pobox.com/~djb/proto/eplf.html
    # "+i8388621.29609,m824255902,/,\tdev"
    # "+i8388621.44468,m839956783,r,s10376,\tRFCEPLF"
    if line[0] == '+':
        if '\t' in line:
            flags, name = line.split('\t', 1)
            info['name'] = name
            flags = flags.split(',')
            info['trycwd'] = '/' in flags
            info['tryretr'] = 'r' in flags
        return info

    # UNIX-style listing, without inum and without blocks
    # "-rw-r--r--   1 root     other        531 Jan 29 03:26 README"
    # "dr-xr-xr-x   2 root     other        512 Apr  8  1994 etc"
    # "dr-xr-xr-x   2 root     512 Apr  8  1994 etc"
    # "lrwxrwxrwx   1 root     other          7 Jan 25 00:17 bin -> usr/bin"
    # Also produced by Microsoft's FTP servers for Windows:
    # "----------   1 owner    group         1803128 Jul 10 10:18 ls-lR.Z"
    # "d---------   1 owner    group               0 May  9 19:45 Softlib"
    # Also WFTPD for MSDOS:
    # "-rwxrwxrwx   1 noone    nogroup      322 Aug 19  1996 message.ftp"
    # Also NetWare:
    # "d [R----F--] supervisor            512       Jan 16 18:53    login"
    # "- [R----F--] rhesus             214059       Oct 20 15:27    cx.exe"
    # Also NetPresenz for the Mac:
    # "-------r--         326  1391972  1392298 Nov 22  1995 MegaPhone.sit"
    # "drwxrwxr-x               folder        2 May 10  1996 network"
    if line[0] in 'bcdlps-':
        if line[0] == 'd':
            info['trycwd'] = True
        if line[0] == '-':
            info['tryretr'] = True
        if line[0] == 'l':
            info['trycwd'] = info['tryretr'] = True
        parts = line.split()
        if len(parts) < 7:
            return None
        del parts[0] # skip permissions
        if parts[0] != 'folder':
            del parts[0] # skip nlink
        del parts[0] # skip uid
        del parts[0] # skip gid or size
        if not ismonth(parts[0]):
            del parts[0] # skip size
        if not ismonth(parts[0]):
            return None
        del parts[0] # skip month
        del parts[0] # skip day
        if not parts:
            return None
        del parts[0] # skip year or time
        name = " ".join(parts)
        # resolve links
        if line[0] == 'l' and ' -> ' in name:
            name = name.split(' -> ', 1)[1]
        # eliminate extra NetWare spaces
        if line[1] in ' [' and name.startswith('   '):
            name = name[3:]
        info["name"] = name
        return info

    # MultiNet (some spaces removed from examples)
    # "00README.TXT;1      2 30-DEC-1996 17:44 [SYSTEM] (RWED,RWED,RE,RE)"
    # "CORE.DIR;1          1  8-SEP-1996 16:09 [SYSTEM] (RWE,RWE,RE,RE)"
    # and non-MutliNet VMS:
    # "CII-MANUAL.TEX;1  213/216  29-JAN-1996 03:33:12  [ANONYMOU,ANONYMOUS]   (RWED,RWED,,)"
    i = line.find(';')
    if i != -1:
        name = line[:i]
        if name.endswith(".DIR"):
            name = name[:-4]
            info["trycwd"] = True
        else:
            info["tryretr"] = True
        info["name"] = name
        return info

    # MSDOS format
    # 04-27-00  09:09PM       <DIR>          licensed
    # 07-18-00  10:16AM       <DIR>          pub
    # 04-14-00  03:47PM                  589 readme.htm
    if line[0].isdigit():
        parts = line.split()
        if len(parts) != 4:
            return None
        info['name'] = parts[3]
        if parts[2][0] == '<':
            info['trycwd'] = True
        else:
            info['tryretr'] = True
        return info

    # Some useless lines, safely ignored:
    # "Total of 11 Files, 10966 Blocks." (VMS)
    # "total 14786" (UNIX)
    # "DISK$ANONFTP:[ANONYMOUS]" (VMS)
    # "Directory DISK$PCSA:[ANONYM]" (VMS)
    return None
