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

import time
import socket
import select
import re
import urlparse
import nntplib
import ftplib
import linkcheck.httplib2
import bk.net.dns.Base


# we catch these exceptions, all other exceptions are internal
# or system errors
ExcList = [
    IOError,
    OSError, # OSError is thrown on Windows when a file is not found
    ValueError, # from httplib.py
    linkcheck.LinkCheckerError,
    bk.net.dns.Base.DNSError,
    socket.timeout,
    socket.error,
    select.error,
    # nttp errors (including EOFError)
    nntplib.error_reply,
    nntplib.error_temp,
    nntplib.error_perm,
    nntplib.error_proto,
    EOFError,
    # http error
    linkcheck.httplib2.error,
    # ftp errors
    ftplib.error_reply,
    ftplib.error_temp,
    ftplib.error_perm,
    ftplib.error_proto,
]
if hasattr(socket, "sslerror"):
    ExcList.append(socket.sslerror)



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
        start_time = time.time()
        status_time = start_time
        while True:
            if config.hasMoreUrls():
                config.checkUrl(config.getUrl())
            elif config.finished():
                break
            else:
                # active connections are downloading/parsing, so
                # wait a little
                time.sleep(0.1)
            if config['status']:
                curtime = time.time()
                if (curtime - status_time) > 5:
                    printStatus(config, curtime, start_time)
                    status_time = curtime
        config.log_endOfOutput()
    except KeyboardInterrupt:
        config.finish()
        config.log_endOfOutput()
        active = config.threader.active_threads()
        linkcheck.log.warn(LOG_CHECK, bk.i18n._("keyboard interrupt; waiting for %d active threads to finish") % active)
        raise


import linkcheck.checker.FileUrlData
import linkcheck.checker.IgnoredUrlData
import linkcheck.checker.FtpUrlData
import linkcheck.checker.GopherUrlData
import linkcheck.checker.HttpUrlData
import linkcheck.checker.HttpsUrlData
import linkcheck.checker.MailtoUrlData
import linkcheck.checker.TelnetUrlData
import linkcheck.checker.NntpUrlData

# file extensions we can parse recursively
extensions = {
    "html": re.compile(r'(?i)\.s?html?$'),
    "opera": re.compile(r'^(?i)opera.adr$'), # opera bookmark file
    "css": re.compile(r'(?i)\.css$'), # CSS stylesheet
#    "text": re.compile(r'(?i)\.(txt|xml|tsv|csv|sgml?|py|java|cc?|cpp|h)$'),
}


def set_intern_url (url, klass, config):
    """Precondition: config['strict'] is true (ie strict checking) and
       recursion level is zero (ie url given on the command line)"""
    if klass == linkcheck.checker.FileUrlData.FileUrlData:
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Add intern pattern ^file:")
        config['internlinks'].append(getLinkPat("^file:"))
    elif klass in [linkcheck.checker.HttpUrlData.HttpUrlData,
                   linkcheck.checker.HttpsUrlData.HttpsUrlData,
                   linkcheck.checker.FtpUrlData.FtpUrlData]:
        domain = urlparse.urlsplit(url)[1]
        if domain:
            domain = "://%s"%re.escape(domain)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Add intern domain", domain)
            # add scheme colon to link pattern
            config['internlinks'].append(getLinkPat(domain))


def getUrlDataFrom (urlName, recursionLevel, config, parentName=None,
                    baseRef=None, line=0, column=0, name=None,
                    cmdline=None):
    url = get_absolute_url(urlName, baseRef, parentName)
    # test scheme
    if url.startswith("http:"):
        klass = linkcheck.checker.HttpUrlData.HttpUrlData
    elif url.startswith("ftp:"):
        klass = linkcheck.checker.FtpUrlData.FtpUrlData
    elif url.startswith("file:"):
        klass = linkcheck.checker.FileUrlData.FileUrlData
    elif url.startswith("telnet:"):
        klass = linkcheck.checker.TelnetUrlData.TelnetUrlData
    elif url.startswith("mailto:"):
        klass = linkcheck.checker.MailtoUrlData.MailtoUrlData
    elif url.startswith("gopher:"):
        klass = linkcheck.checker.GopherUrlData.GopherUrlData
    elif url.startswith("https:"):
        klass = linkcheck.checker.HttpsUrlData.HttpsUrlData
    elif url.startswith("nttp:") or \
         url.startswith("news:") or \
         url.startswith("snews:"):
        klass = linkcheck.checker.NntpUrlData.NntpUrlData
    # application specific links are ignored
    elif ignored_schemes_re.search(url):
        klass = linkcheck.checker.IgnoredUrlData.IgnoredUrlData
    # assume local file
    else:
        klass = linkcheck.checker.FileUrlData.FileUrlData
    if config['strict'] and cmdline and \
       not (config['internlinks'] or config['externlinks']):
        # set automatic intern/extern stuff if no filter was given
        set_intern_url(url, klass, config)
    return klass(urlName, recursionLevel, config, parentName, baseRef,
                 line=line, column=column, name=name)
