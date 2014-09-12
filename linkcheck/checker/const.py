# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
Helper constants.
"""
import socket
import select
import nntplib
import ftplib
import requests
from .. import LinkCheckerError
from dns.exception import DNSException

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
    nntplib.NNTPError,
    EOFError,
    # http errors
    requests.exceptions.RequestException,
    requests.packages.urllib3.exceptions.HTTPError,
    # ftp errors
    ftplib.Error,
    # idna.encode(), called from socket.create_connection()
    UnicodeError,
]

# Exceptions that do not put the URL in the cache so that the URL can
# be checked again.
ExcNoCacheList = [
    socket.timeout,
]

# firefox bookmark file needs sqlite3 for parsing
try:
    import sqlite3
    ExcCacheList.append(sqlite3.Error)
except ImportError:
    pass

# pyOpenSSL errors
try:
    import OpenSSL
    ExcCacheList.append(OpenSSL.SSL.Error)
except ImportError:
    pass


ExcList = ExcCacheList + ExcNoCacheList

# Maximum URL length
# https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
URL_MAX_LENGTH = 2047

# the warnings
WARN_URL_EFFECTIVE_URL = "url-effective-url"
WARN_URL_ERROR_GETTING_CONTENT = "url-error-getting-content"
WARN_URL_CONTENT_SIZE_TOO_LARGE = "url-content-too-large"
WARN_URL_CONTENT_SIZE_ZERO = "url-content-size-zero"
WARN_URL_OBFUSCATED_IP = "url-obfuscated-ip"
WARN_URL_TOO_LONG = "url-too-long"
WARN_URL_WHITESPACE = "url-whitespace"
WARN_FILE_MISSING_SLASH = "file-missing-slash"
WARN_FILE_SYSTEM_PATH = "file-system-path"
WARN_FTP_MISSING_SLASH = "ftp-missing-slash"
WARN_HTTP_EMPTY_CONTENT = "http-empty-content"
WARN_HTTP_COOKIE_STORE_ERROR = "http-cookie-store-error"
WARN_IGNORE_URL = "ignore-url"
WARN_MAIL_NO_MX_HOST = "mail-no-mx-host"
WARN_NNTP_NO_SERVER = "nntp-no-server"
WARN_NNTP_NO_NEWSGROUP = "nntp-no-newsgroup"
WARN_XML_PARSE_ERROR = "xml-parse-error"

# registered warnings
Warnings = {
    WARN_URL_EFFECTIVE_URL:
        _("The effective URL is different from the original."),
    WARN_URL_ERROR_GETTING_CONTENT:
        _("Could not get the content of the URL."),
    WARN_URL_CONTENT_SIZE_TOO_LARGE: _("The URL content size is too large."),
    WARN_URL_CONTENT_SIZE_ZERO: _("The URL content size is zero."),
    WARN_URL_TOO_LONG: _("The URL is longer than the recommended size."),
    WARN_URL_WHITESPACE: _("The URL contains leading or trailing whitespace."),
    WARN_FILE_MISSING_SLASH: _("The file: URL is missing a trailing slash."),
    WARN_FILE_SYSTEM_PATH:
        _("The file: path is not the same as the system specific path."),
    WARN_FTP_MISSING_SLASH: _("The ftp: URL is missing a trailing slash."),
    WARN_HTTP_EMPTY_CONTENT: _("The URL had no content."),
    WARN_HTTP_COOKIE_STORE_ERROR:
        _("An error occurred while storing a cookie."),
    WARN_IGNORE_URL: _("The URL has been ignored."),
    WARN_MAIL_NO_MX_HOST: _("The mail MX host could not be found."),
    WARN_NNTP_NO_SERVER: _("No NNTP server was found."),
    WARN_NNTP_NO_NEWSGROUP: _("The NNTP newsgroup could not be found."),
    WARN_URL_OBFUSCATED_IP: _("The IP is obfuscated."),
    WARN_XML_PARSE_ERROR: _("XML could not be parsed."),
}
