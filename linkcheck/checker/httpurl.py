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
Handle http links.
"""

import requests
from cStringIO import StringIO

from .. import (log, LOG_CHECK, strformat,
    url as urlutil, LinkCheckerError)
from . import (internpaturl, proxysupport, httpheaders as headers)
# import warnings
from .const import WARN_HTTP_EMPTY_CONTENT

# assumed HTTP header encoding
HEADER_ENCODING = "iso-8859-1"
HTTP_SCHEMAS = ('http://', 'https://')

# helper alias
unicode_safe = strformat.unicode_safe

class HttpUrl (internpaturl.InternPatternUrl, proxysupport.ProxySupport):
    """
    Url link with http scheme.
    """

    def reset (self):
        """
        Initialize HTTP specific variables.
        """
        super(HttpUrl, self).reset()
        # URLs seen through redirections
        self.aliases = []
        # initialize check data
        self.headers = {}
        self.auth = None

    def allows_robots (self, url):
        """
        Fetch and parse the robots.txt of given url. Checks if LinkChecker
        can get the requested resource content.

        @param url: the url to be requested
        @type url: string
        @return: True if access is granted, otherwise False
        @rtype: bool
        """
        return self.aggregate.robots_txt.allows_url(self)

    def add_size_info (self):
        """Get size of URL content from HTTP header."""
        if self.headers and "Content-Length" in self.headers and \
           "Transfer-Encoding" not in self.headers:
            # Note that content-encoding causes size differences since
            # the content data is always decoded.
            try:
                self.size = int(self.getheader("Content-Length"))
            except (ValueError, OverflowError):
                pass
        else:
            self.size = -1

    def check_connection (self):
        """
        Check a URL with HTTP protocol.
        Here is an excerpt from RFC 1945 with common response codes:
        The first digit of the Status-Code defines the class of response. The
        last two digits do not have any categorization role. There are 5
        values for the first digit:
          - 1xx: Informational - Not used, but reserved for future use
          - 2xx: Success - The action was successfully received,
            understood, and accepted.
          - 3xx: Redirection - Further action must be taken in order to
            complete the request
          - 4xx: Client Error - The request contains bad syntax or cannot
            be fulfilled
          - 5xx: Server Error - The server failed to fulfill an apparently
            valid request
        """
        self.session = self.aggregate.get_request_session()
        # set the proxy, so a 407 status after this is an error
        self.set_proxy(self.aggregate.config["proxy"].get(self.scheme))
        self.construct_auth()
        # check robots.txt
        if not self.allows_robots(self.url):
            self.add_info(_("Access denied by robots.txt, checked only syntax."))
            self.set_result(_("syntax OK"))
            self.do_check_content = False
            return
        # check the http connection
        request = self.build_request()
        self.send_request(request)
        self.follow_redirections(request)
        self.check_response()

    def build_request(self):
        """Build a prepared request object."""
        clientheaders = {
            "User-Agent": self.aggregate.config["useragent"],
            "DNT": "1",
        }
        if (self.parent_url and
            self.parent_url.lower().startswith(HTTP_SCHEMAS)):
            clientheaders["Referer"] = self.parent_url
        kwargs = dict(
            method='GET',
            url=self.url,
            headers=clientheaders,
        )
        if self.auth:
            kwargs['auth'] = self.auth
        log.debug(LOG_CHECK, "Prepare request with %s", kwargs)
        request = requests.Request(**kwargs)
        return self.session.prepare_request(request)

    def send_request(self, request):
        """Send request and store response in self.url_connection."""
        # throttle the number of requests to each host
        self.aggregate.wait_for_host(self.urlparts[1])
        kwargs = dict(
            stream=True,
            timeout=self.aggregate.config["timeout"],
            allow_redirects=False,
        )
        if self.scheme == "https" and self.aggregate.config["sslverify"]:
            kwargs["verify"] = self.aggregate.config["sslverify"]
        log.debug(LOG_CHECK, "Send request with %s", kwargs)
        self.url_connection = self.session.send(request, **kwargs)
        self.headers = self.url_connection.headers

    def construct_auth (self):
        """Construct HTTP Basic authentication credentials if there
        is user/password information available. Does not overwrite if
        credentials have already been constructed."""
        if self.auth:
            return
        _user, _password = self.get_user_password()
        if _user is not None and _password is not None:
            self.auth = (_user, _password)

    def get_content_type (self):
        """Return content MIME type or empty string."""
        if not self.content_type:
            self.content_type = headers.get_content_type(self.headers)
        return self.content_type

    def follow_redirections(self, request):
        """Follow all redirections of http response."""
        log.debug(LOG_CHECK, "follow all redirections")
        kwargs = dict(
            stream=True,
        )
        response = None
        for response in self.session.resolve_redirects(self.url_connection, request, **kwargs):
            newurl = response.url
            log.debug(LOG_CHECK, "Redirected to %r", newurl)
            self.aliases.append(newurl)
            self.add_info(_("Redirected to `%(url)s'.") % {'url': newurl})
            urlparts = strformat.url_unicode_split(newurl)
        if response is not None:
            self.urlparts = urlparts
            self.build_url_parts()
            self.url_connection = response
            self.headers = response.headers
            self.url = urlutil.urlunsplit(urlparts)
            self.scheme = urlparts[0].lower()

    def getheader (self, name, default=None):
        """Get decoded header value.

        @return: decoded header value or default of not found
        @rtype: unicode or type of default
        """
        value = self.headers.get(name)
        if value is None:
            return default
        return unicode_safe(value, encoding=HEADER_ENCODING)

    def check_response (self):
        """Check final result and log it."""
        if self.url_connection.status_code >= 400:
            self.set_result(u"%d %s" % (self.url_connection.status_code, self.url_connection.reason),
                            valid=False)
        else:
            if self.url_connection.status_code == 204:
                # no content
                self.add_warning(self.url_connection.reason,
                                 tag=WARN_HTTP_EMPTY_CONTENT)
            if self.url_connection.status_code >= 200:
                self.set_result(u"%r %s" % (self.url_connection.status_code, self.url_connection.reason))
            else:
                self.set_result(_("OK"))

    def read_content(self):
        """Return data and data size for this URL.
        Can be overridden in subclasses."""
        maxbytes = self.aggregate.config["maxfilesizedownload"]
        buf = StringIO()
        for data in self.url_connection.iter_content(chunk_size=self.ReadChunkBytes):
            if buf.tell() + len(data) > maxbytes:
                raise LinkCheckerError(_("File size too large"))
            buf.write(data)
        return buf.getvalue()

    def is_html (self):
        """
        See if this URL points to a HTML file by looking at the
        Content-Type header, file extension and file content.

        @return: True if URL points to HTML file
        @rtype: bool
        """
        if not self.valid:
            return False
        mime = self.get_content_type()
        return self.ContentMimetypes.get(mime) == "html"

    def is_css (self):
        """Return True iff content of this url is CSS stylesheet."""
        if not self.valid:
            return False
        mime = self.get_content_type()
        return self.ContentMimetypes.get(mime) == "css"

    def is_http (self):
        """
        This is a HTTP file.

        @return: True
        @rtype: bool
        """
        return True

    def is_parseable (self):
        """
        Check if content is parseable for recursion.

        @return: True if content is parseable
        @rtype: bool
        """
        if not self.valid:
            return False
        ctype = self.get_content_type()
        if ctype not in self.ContentMimetypes:
            log.debug(LOG_CHECK, "URL with content type %r is not parseable", ctype)
            return False
        return True

    def get_robots_txt_url (self):
        """
        Get the according robots.txt URL for this URL.

        @return: robots.txt URL
        @rtype: string
        """
        return "%s://%s/robots.txt" % tuple(self.urlparts[0:2])
