# -*- coding: iso-8859-1 -*-
# Copyright (C) 2005-2007 Bastian Kleineidam
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
Helper functions dealing with HTTP headers.
"""

DEFAULT_TIMEOUT_SECS = 300

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


def http_timeout (response):
    """
    Get HTTP timeout value, either from the Keep-Alive header or a
    default value.

    @param response: response instance
    @type response: httplib.HTTPResponse
    @return: timeout
    @rtype: int
    """
    timeout = response.getheader("Keep-Alive")
    if timeout is not None:
        try:
            timeout = int(timeout[8:].strip())
        except ValueError, msg:
            timeout = DEFAULT_TIMEOUT_SECS
    else:
        timeout = DEFAULT_TIMEOUT_SECS
    return timeout


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
    return ptype.strip()


def get_content_encoding (headers):
    """
    Get the content encoding from the Content-Encoding header value, or
    an empty string if not found.

    @return: encoding string
    @rtype: string
    """
    return headers.get("Content-Encoding", "").strip()
