"""internationalization support"""
# Copyright (C) 2000-2002  Bastian Kleineidam
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

# i18n suppport
import os
from _linkchecker_configdata import install_data

def init_gettext ():
    global _
    try:
        import gettext
        domain = 'linkcheck'
        localedir = os.path.join(install_data, 'share/locale')
        _ = gettext.translation(domain, localedir).gettext
    except (IOError, ImportError):
        # default gettext function
        _ = lambda s: s

init_gettext()
