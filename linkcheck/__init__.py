# -*- coding: iso-8859-1 -*-
"""main function module for link checking"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import re
import sys
import urlparse


# logger areas
LOG_CMDLINE = "linkcheck.cmdline"
LOG_CHECK = "linkcheck.check"
LOG_DNS = "linkcheck.dns"
LOG_GUI = "linkcheck.gui"


class LinkCheckerError (Exception):
    pass


def getLinkPat (arg, strict=False):
    """get a link pattern matcher for intern/extern links"""
    linkcheck.log.debug(LOG_CHECK, "Link pattern %r", arg)
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


import linkcheck.FileUrlData
import linkcheck.IgnoredUrlData
import linkcheck.FtpUrlData
import linkcheck.GopherUrlData
import linkcheck.HttpUrlData
import linkcheck.HttpsUrlData
import linkcheck.MailtoUrlData
import linkcheck.TelnetUrlData
import linkcheck.NntpUrlData

def set_intern_url (url, klass, config):
    """Precondition: config['strict'] is true (ie strict checking) and
       recursion level is zero (ie url given on the command line)"""
    if klass == linkcheck.FileUrlData.FileUrlData:
        linkcheck.log.debug(LOG_CHECK, "Add intern pattern ^file:")
        config['internlinks'].append(getLinkPat("^file:"))
    elif klass in [linkcheck.HttpUrlData.HttpUrlData,
                   linkcheck.HttpsUrlData.HttpsUrlData,
                   linkcheck.FtpUrlData.FtpUrlData]:
        domain = urlparse.urlsplit(url)[1]
        if domain:
            domain = "://%s"%re.escape(domain)
            debug(BRING_IT_ON, "Add intern domain", domain)
            # add scheme colon to link pattern
            config['internlinks'].append(getLinkPat(domain))


import linkcheck.logger

def printStatus (config, curtime, start_time):
    tocheck = len(config.urls)
    links = config['linknumber']
    active = config.threader.active_threads()
    duration = linkcheck.logger.strduration(curtime - start_time)
    print >>sys.stderr, linkcheck.i18n._("%5d urls queued, %4d links checked, %2d active threads, runtime %s")%\
                               (tocheck, links, active, duration)
