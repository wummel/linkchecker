# -*- coding: iso-8859-1 -*-
"""main function module for link checking"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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

class LinkCheckerError (Exception):
    pass

import re, i18n
def getLinkPat (arg, strict=False):
    """get a link pattern matcher for intern/extern links"""
    debug(BRING_IT_ON, "Link pattern %r", arg)
    if arg[0:1] == '!':
        pattern = arg[1:]
        negate = True
    else:
        pattern = arg
        negate = False
    return {
        "pattern": re.compile(pattern),
        "negate": negate,
        "strict": strict,
    }

# file extensions we can parse recursively
extensions = {
    "html": re.compile(r'(?i)\.s?html?$'),
    "opera": re.compile(r'^(?i)opera.adr$'), # opera bookmark file
    "css": re.compile(r'(?i)\.css$'), # CSS stylesheet
#    "text": re.compile(r'(?i)\.(txt|xml|tsv|csv|sgml?|py|java|cc?|cpp|h)$'),
}

import UrlData
from debug import *

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
        warn(i18n._("keyboard interrupt; waiting for active connections to finish"))
        raise
