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
import sys
import socket
import select
import re
import urlparse
import nntplib
import ftplib

import linkcheck.httplib2
import linkcheck.dns.exception

from linkcheck.i18n import _


# we catch these exceptions, all other exceptions are internal
# or system errors
ExcList = [
    IOError,
    OSError, # OSError is thrown on Windows when a file is not found
    ValueError, # from httplib.py
    linkcheck.LinkCheckerError,
    linkcheck.dns.exception.DNSException,
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


#_schemes = r"""(
#acap        # application configuration access protocol
#|afs        # Andrew File System global file names
#|cid        # content identifier
#|data       # data
#|dav        # dav
#|fax        # fax
#|imap       # internet message access protocol
#|ldap       # Lightweight Directory Access Protocol
#|mailserver # Access to data available from mail servers
#|mid        # message identifier
#|modem      # modem
#|nfs        # network file system protocol
#|opaquelocktoken # opaquelocktoken
#|pop        # Post Office Protocol v3
#|prospero   # Prospero Directory Service
#|rtsp       # real time streaming protocol
#|service    # service location
#|sip        # session initiation protocol
#|tel        # telephone
#|tip        # Transaction Internet Protocol
#|tn3270     # Interactive 3270 emulation sessions
#|vemmi      # versatile multimedia interface
#|wais       # Wide Area Information Servers
#|z39\.50r   # Z39.50 Retrieval
#|z39\.50s   # Z39.50 Session
#|chrome     # Mozilla specific
#|find       # Mozilla specific
#|clsid      # Microsoft specific
#|javascript # JavaScript
#|isbn       # ISBN (int. book numbers)
#|https?     # HTTP/HTTPS
#|ftp        # FTP
#|file       # local file
#|telnet     # telnet
#|mailto     # mailto
#|gopher     # gopher
#|s?news     # news
#|nntp       # news
#)"""

ignored_schemes = r"""^(
acap        # application configuration access protocol
|afs        # Andrew File System global file names
|cid        # content identifier
|data       # data
|dav        # dav
|fax        # fax
|imap       # internet message access protocol
|ldap       # Lightweight Directory Access Protocol
|mailserver # Access to data available from mail servers
|mid        # message identifier
|modem      # modem
|nfs        # network file system protocol
|opaquelocktoken # opaquelocktoken
|pop        # Post Office Protocol v3
|prospero   # Prospero Directory Service
|rtsp       # real time streaming protocol
|service    # service location
|sip        # session initiation protocol
|tel        # telephone
|tip        # Transaction Internet Protocol
|tn3270     # Interactive 3270 emulation sessions
|vemmi      # versatile multimedia interface
|wais       # Wide Area Information Servers
|z39\.50r   # Z39.50 Retrieval
|z39\.50s   # Z39.50 Session
|chrome     # Mozilla specific
|find       # Mozilla specific
|clsid      # Microsoft specific
|javascript # JavaScript
|isbn       # ISBN (int. book numbers)
):"""

ignored_schemes_re = re.compile(ignored_schemes, re.VERBOSE)


# main check function
def check_urls (consumer):
    """Gets a complete configuration object as parameter where all
       runtime-dependent options are stored. If you call this function
       more than once, you can specify different configurations.
    """
    try:
        _check_urls(consumer)
    except KeyboardInterrupt:
        consumer.finish()
        linkcheck.log.warn(linkcheck.LOG_CHECK,
             _("keyboard interrupt; waiting for %d active threads to finish"),
             consumer.active_threads())
        raise


def _check_urls (consumer):
    consumer.logger_start_output()
    start_time = time.time()
    status_time = start_time
    while not consumer.finished():
        url = consumer.get_url()
        if url is not None:
            consumer.check_url(url)
        else:
            # active connections are downloading/parsing, so
            # wait a little
            time.sleep(0.1)
        if consumer.config['status']:
            curtime = time.time()
            if (curtime - status_time) > 5:
                consumer.print_status(curtime, start_time)
                status_time = curtime
    consumer.logger_end_output()


# file extensions we can parse recursively
extensions = {
    "html": re.compile(r'(?i)\.s?html?$'),
    "opera": re.compile(r'^(?i)opera.adr$'), # opera bookmark file
    "css": re.compile(r'(?i)\.css$'), # CSS stylesheet
#    "text": re.compile(r'(?i)\.(txt|xml|tsv|csv|sgml?|py|java|cc?|cpp|h)$'),
}


import linkcheck.checker.fileurl
import linkcheck.checker.ignoredurl
import linkcheck.checker.ftpurl
import linkcheck.checker.gopherurl
import linkcheck.checker.httpurl
import linkcheck.checker.httpsurl
import linkcheck.checker.mailtourl
import linkcheck.checker.telneturl
import linkcheck.checker.nntpurl


def set_intern_url (url, klass, config):
    """add intern url pattern for url given on the command line"""
    if klass == linkcheck.checker.fileurl.FileUrl:
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Add intern pattern ^file:")
        config['internlinks'].append(linkcheck.get_link_pat("^file:"))
    elif klass in [linkcheck.checker.httpurl.HttpUrl,
                   linkcheck.checker.httpsurl.HttpsUrl,
                   linkcheck.checker.ftpurl.FtpUrl]:
        domain = urlparse.urlsplit(url)[1]
        if domain:
            domain = "://%s" % re.escape(domain)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Add intern domain %r",
                                domain)
            # add scheme colon to link pattern
            config['internlinks'].append(linkcheck.get_link_pat(domain))


def absolute_url (base_url, base_ref, parent_url):
    """Search for the absolute url to detect the link type. This does not
       join any url fragments together! Returns the url in lower case to
       simplify urltype matching."""
    if base_url and ":" in base_url:
        return base_url.lower()
    elif base_ref and ":" in base_ref:
        return base_ref.lower()
    elif parent_url and ":" in parent_url:
        return parent_url.lower()
    return ""


def get_url_from (base_url, recursion_level, consumer,
                  parent_url=None, base_ref=None, line=0, column=0,
                  name=None, cmdline=None):
    """get url data from given base data"""
    if cmdline and linkcheck.url.url_needs_quoting(base_url):
        base_url = linkcheck.url.url_quote(base_url)
    url = absolute_url(base_url, base_ref, parent_url)
    # test scheme
    if url.startswith("http:"):
        klass = linkcheck.checker.httpurl.HttpUrl
    elif url.startswith("ftp:"):
        klass = linkcheck.checker.ftpurl.FtpUrl
    elif url.startswith("file:"):
        klass = linkcheck.checker.fileurl.FileUrl
    elif url.startswith("telnet:"):
        klass = linkcheck.checker.telneturl.TelnetUrl
    elif url.startswith("mailto:"):
        klass = linkcheck.checker.mailtourl.MailtoUrl
    elif url.startswith("gopher:"):
        klass = linkcheck.checker.gopherurl.GopherUrl
    elif url.startswith("https:"):
        klass = linkcheck.checker.httpsurl.HttpsUrl
    elif url.startswith("nntp:") or \
         url.startswith("news:") or \
         url.startswith("snews:"):
        klass = linkcheck.checker.nntpurl.NntpUrl
    # application specific links are ignored
    elif ignored_schemes_re.search(url):
        klass = linkcheck.checker.ignoredurl.IgnoredUrl
    # assume local file
    else:
        klass = linkcheck.checker.fileurl.FileUrl
    if cmdline and not (consumer.config['internlinks'] or
                        consumer.config['externlinks']):
        # set automatic intern/extern stuff if no filter was given
        set_intern_url(base_url, klass, consumer.config)
    return klass(base_url, recursion_level, consumer,
                 parent_url=parent_url, base_ref=base_ref,
                 line=line, column=column, name=name)
