# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2014 Bastian Kleineidam
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
Helper functions dealing with HTTP headers.
"""

DEFAULT_KEEPALIVE = 300

MAX_HEADER_BYTES = 8*1024

def has_header_value (headers, name, value):
    """
    Look in headers for a specific header name and value.
    Both name and value are case insensitive.

    @return: True if header name and value are found
    @rtype: bool
    """
    name = name.lower()
    value = value.lower()
    for hname, hvalue in headers:
        if hname.lower()==name and hvalue.lower()==value:
            return True
    return False


def http_persistent (response):
    """
    See if the HTTP connection can be kept open according the the
    header values found in the response object.

    @param response: response instance
    @type response: httplib.HTTPResponse
    @return: True if connection is persistent
    @rtype: bool
    """
    headers = response.getheaders()
    if response.version == 11:
        return not has_header_value(headers, 'Connection', 'Close')
    return has_header_value(headers, "Connection", "Keep-Alive")


def http_keepalive (headers):
    """
    Get HTTP keepalive value, either from the Keep-Alive header or a
    default value.

    @param headers: HTTP headers
    @type headers: dict
    @return: keepalive in seconds
    @rtype: int
    """
    keepalive = headers.get("Keep-Alive")
    if keepalive is not None:
        try:
            keepalive = int(keepalive[8:].strip())
        except (ValueError, OverflowError):
            keepalive = DEFAULT_KEEPALIVE
    else:
        keepalive = DEFAULT_KEEPALIVE
    return keepalive


def get_content_type (headers):
    """
    Get the MIME type from the Content-Type header value, or
    'application/octet-stream' if not found.

    @return: MIME type
    @rtype: string
    """
    ptype = headers.get('Content-Type', 'application/octet-stream')
    if ";" in ptype:
        # split off not needed extension info
        ptype = ptype.split(';')[0]
    return ptype.strip().lower()


def get_charset(headers):
    """
    Get the charset encoding from the Content-Type header value, or
    None if not found.

    @return: the content charset encoding
    @rtype: string or None
    """
    from linkcheck.HtmlParser import get_ctype_charset
    return get_ctype_charset(headers.get('Content-Type', ''))


def get_content_encoding (headers):
    """
    Get the content encoding from the Content-Encoding header value, or
    an empty string if not found.

    @return: encoding string
    @rtype: string
    """
    return headers.get("Content-Encoding", "").strip()
