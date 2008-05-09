# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
"""
Helper constants.
"""
import socket
import select
import nntplib
import ftplib
import re
from .. import LinkCheckerError, httplib2 as httplib
from ..dns.exception import DNSException

# Catch these exception on syntax checks.
ExcSyntaxList = [
    LinkCheckerError,
]

# Catch these exceptions on content and connect checks. All other
# exceptions are internal or system errors
ExcCacheList = [
    IOError,
    OSError, # OSError is thrown on Windows when a file is not found
    LinkCheckerError,
    DNSException,
    socket.error,
    select.error,
    # nttp errors (including EOFError)
    nntplib.error_reply,
    nntplib.error_temp,
    nntplib.error_perm,
    nntplib.error_proto,
    EOFError,
    # http error
    httplib.error,
    # ftp errors
    ftplib.error_reply,
    ftplib.error_temp,
    ftplib.error_perm,
    ftplib.error_proto,
]

# Exceptions that do not put the URL in the cache so that the URL can
# be checked again.
ExcNoCacheList = [
    socket.timeout,
]

ExcList = ExcCacheList + ExcNoCacheList

WARN_URL_EFFECTIVE_URL = "url-effective-url"
WARN_URL_ERROR_GETTING_CONTENT = "url-error-getting-content"
WARN_URL_UNICODE_DOMAIN = "url-unicode-domain"
WARN_URL_UNNORMED = "url-unnormed"
WARN_URL_ANCHOR_NOT_FOUND = "url-anchor-not-found"
WARN_URL_WARNREGEX_FOUND = "url-warnregex-found"
WARN_URL_CONTENT_TOO_LARGE = "url-content-too-large"
WARN_FILE_MISSING_SLASH = "file-missing-slash"
WARN_FILE_SYSTEM_PATH = "file-system-path"
WARN_FTP_MISSING_SLASH = "ftp-missing-slash"
WARN_HTTP_ROBOTS_DENIED = "http-robots-denied"
WARN_HTTP_NO_ANCHOR_SUPPORT = "http-no-anchor-support"
WARN_HTTP_MOVED_PERMANENT = "http-moved-permanent"
WARN_HTTP_WRONG_REDIRECT = "http-wrong-redirect"
WARN_HTTP_EMPTY_CONTENT = "http-empty-content"
WARN_HTTP_COOKIE_STORE_ERROR = "http-cookie-store-error"
WARN_HTTP_DECOMPRESS_ERROR = "http-decompress-error"
WARN_HTTP_UNSUPPORTED_ENCODING = "http-unsupported-encoding"
WARN_IGNORE_URL = "ignore-url"
WARN_MAIL_NO_ADDRESSES = "mail-no-addresses"
WARN_MAIL_NO_MX_HOST = "mail-no-mx-host"
WARN_MAIL_UNVERIFIED_ADDRESS = "mail-unverified-address"
WARN_MAIL_NO_CONNECTION = "mail-no-connection"
WARN_NNTP_NO_SERVER = "nntp-no-server"
WARN_NNTP_NO_NEWSGROUP = "nntp-no-newsgroup"
WARN_NNTP_BUSY = "nntp-busy"

# registered warnings
Warnings = {
    WARN_URL_EFFECTIVE_URL:
        _("The effective URL is different from the original."),
    WARN_URL_ERROR_GETTING_CONTENT:
        _("Could not get the content of the URL."),
    WARN_URL_UNICODE_DOMAIN: _("URL uses a unicode domain."),
    WARN_URL_UNNORMED: _("URL is not normed."),
    WARN_URL_ANCHOR_NOT_FOUND: _("URL anchor was not found."),
    WARN_URL_WARNREGEX_FOUND:
        _("The warning regular expression was found in the URL contents."),
    WARN_URL_CONTENT_TOO_LARGE: _("The URL content is too large."),
    WARN_FILE_MISSING_SLASH: _("The file: URL is missing a trailing slash."),
    WARN_FILE_SYSTEM_PATH:
        _("The file: path is not the same as the system specific path."),
    WARN_FTP_MISSING_SLASH: _("The ftp: URL is missing a trailing slash."),
    WARN_HTTP_ROBOTS_DENIED: _("The http: URL checking has been denied."),
    WARN_HTTP_NO_ANCHOR_SUPPORT: _("The HTTP server had no anchor support."),
    WARN_HTTP_MOVED_PERMANENT: _("The URL has moved permanently."),
    WARN_HTTP_WRONG_REDIRECT:
        _("The URL has been redirected to an URL of a different type."),
    WARN_HTTP_EMPTY_CONTENT: _("The URL had no content."),
    WARN_HTTP_COOKIE_STORE_ERROR:
        _("An error occurred while storing a cookie."),
    WARN_HTTP_DECOMPRESS_ERROR:
        _("An error occurred while decompressing the URL content."),
    WARN_HTTP_UNSUPPORTED_ENCODING:
        _("The URL content is encoded with an unknown encoding."),
    WARN_IGNORE_URL: _("The URL has been ignored."),
    WARN_MAIL_NO_ADDRESSES: _("The mailto: URL contained no addresses."),
    WARN_MAIL_NO_MX_HOST: _("The mail MX host could not be found."),
    WARN_MAIL_UNVERIFIED_ADDRESS:
        _("The mailto: address could not be verified."),
    WARN_MAIL_NO_CONNECTION:
        _("No connection to a MX host could be established."),
    WARN_NNTP_NO_SERVER: _("No NNTP server was found."),
    WARN_NNTP_NO_NEWSGROUP: _("The NNTP newsgroup could not be found."),
    WARN_NNTP_BUSY: _("The NNTP server was busy."),
}

# file extensions we can parse recursively
PARSE_EXTENSIONS = {
    "html": re.compile(r'(?i)\.s?html?$'),
    "opera": re.compile(r'^(?i)opera.adr$'), # opera bookmark file
    "css": re.compile(r'(?i)\.css$'), # CSS stylesheet
    "swf": re.compile(r'(?i)\.swf$'), # SWF file
}

PARSE_MIMETYPES = (
    "text/html",
    "text/css",
    "application/x-shockwave-flash",
)

# if file extension lookup was unsuccessful, look at the content
PARSE_CONTENTS = {
    "html": re.compile(r'^(?i)<(!DOCTYPE html|html|head|title)'),
    "opera" : re.compile(r'^Opera Hotlist'),
    "text" : re.compile(r'(?i)^# LinkChecker URL list'),
}
