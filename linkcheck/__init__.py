"""main function module for link checking"""
# Copyright (C) 2000,2001  Bastian Kleineidam
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

class error (Exception):
    pass

import re
def getLinkPat (arg, strict=0):
    """get a link pattern matcher for intern/extern links"""
    debug(BRING_IT_ON, "Link pattern", `arg`)
    if arg[0:1] == '!':
        pattern = arg[1:]
        negate = 1
    else:
        pattern = arg
        negate = 0
    return {
        "pattern": re.compile(pattern),
        "negate": negate,
        "strict": strict,
    }

# file extensions we can parse recursively
extensions = {
    "html": r'(?i)\.s?html?$',
    "opera": r'^(?i)opera.adr$', # opera bookmark file
#    "text": r'(?i)\.(txt|xml|tsv|csv|sgml?|py|java|cc?|cpp|h)$',
}
for key in extensions.keys():
    extensions[key] = re.compile(extensions[key])


# i18n suppport
import sys, os, _linkchecker_configdata
def init_gettext ():
    global _
    try:
        import gettext
        domain = 'linkcheck'
        localedir = os.path.join(_linkchecker_configdata.install_data,
                    'share/locale')
        _ = gettext.translation(domain, localedir).gettext
    except (IOError, ImportError):
        _ = lambda s: s
init_gettext()

import Config, UrlData
from debuglevels import *
debug = Config.debug


# main check function
def checkUrls (config):
    """ checkUrls gets a complete configuration object as parameter where all
    runtime-dependent options are stored.
    If you call checkUrls more than once, you can specify different
    configurations.

    In the config object there are functions to get a new URL (getUrl) and
    to check it (checkUrl).
    """
    config.log_init()
    try:
        while not config.finished():
            if config.hasMoreUrls():
                config.checkUrl(config.getUrl())
        config.log_endOfOutput()
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        config.warn(_("keyboard interrupt"))
        raise
