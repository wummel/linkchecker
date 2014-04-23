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

from .. import (log, LOG_CHECK, strformat, fileutil,
    url as urlutil, LinkCheckerError, httputil)
from . import (internpaturl, proxysupport)
from ..HtmlParser import htmlsax
from ..htmlutil import linkparse
# import warnings
from .const import WARN_HTTP_EMPTY_CONTENT
from requests.sessions import REDIRECT_STATI

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
        # initialize check data
        self.headers = {}
        self.auth = None
        self.ssl_cipher = None
        self.ssl_cert = None

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

    def content_allows_robots (self):
        """
        Return False if the content of this URL forbids robots to
        search for recursive links.
        """
        if not self.is_html():
            return True
        # construct parser object
        handler = linkparse.MetaRobotsFinder()
        parser = htmlsax.parser(handler)
        handler.parser = parser
        if self.charset:
            parser.encoding = self.charset
        # parse
        try:
            parser.feed(self.get_content())
            parser.flush()
        except linkparse.StopParse as msg:
            log.debug(LOG_CHECK, "Stopped parsing: %s", msg)
            pass
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        return handler.follow

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
        self._add_response_info()
        self.follow_redirections(request)
        self.check_response()
        if self.allows_simple_recursion():
            self.parse_header_links()

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
        kwargs = self.get_request_kwargs()
        kwargs["allow_redirects"] = False
        self._send_request(request, **kwargs)

    def _send_request(self, request, **kwargs):
        """Send GET request."""
        log.debug(LOG_CHECK, "Send request with %s", kwargs)
        self.url_connection = self.session.send(request, **kwargs)
        self.headers = self.url_connection.headers
        self._add_ssl_info()

    def _add_response_info(self):
        """Set info from established HTTP(S) connection."""
        self.charset = httputil.get_charset(self.headers)
        self.set_content_type()
        self.add_size_info()

    def _get_ssl_sock(self):
        """Get raw SSL socket."""
        assert self.scheme == u"https", self
        raw_connection = self.url_connection.raw._connection
        if raw_connection.sock is None:
            # sometimes the socket is not yet connected
            # see https://github.com/kennethreitz/requests/issues/1966
            raw_connection.connect()
        return raw_connection.sock

    def _add_ssl_info(self):
        """Add SSL cipher info."""
        if self.scheme == u'https':
            sock = self._get_ssl_sock()
            if hasattr(sock, 'cipher'):
                self.ssl_cert = sock.getpeercert()
            else:
                # using pyopenssl
                cert = sock.connection.get_peer_certificate()
                self.ssl_cert = httputil.x509_to_dict(cert)
            log.debug(LOG_CHECK, "Got SSL certificate %s", self.ssl_cert)
        else:
            self.ssl_cert = None

    def construct_auth (self):
        """Construct HTTP Basic authentication credentials if there
        is user/password information available. Does not overwrite if
        credentials have already been constructed."""
        if self.auth:
            return
        _user, _password = self.get_user_password()
        if _user is not None and _password is not None:
            self.auth = (_user, _password)

    def set_content_type (self):
        """Return content MIME type or empty string."""
        self.content_type = httputil.get_content_type(self.headers)

    def is_redirect(self):
        """Check if current response is a redirect."""
        return ('location' in self.headers and
                self.url_connection.status_code in REDIRECT_STATI)

    def get_request_kwargs(self):
        """Construct keyword parameters for Session.request() and
        Session.resolve_redirects()."""
        kwargs = dict(stream=True, timeout=self.aggregate.config["timeout"])
        if self.scheme == u"https" and self.aggregate.config["sslverify"]:
            kwargs['verify'] = self.aggregate.config["sslverify"]
        else:
            kwargs['verify'] = False
        return kwargs

    def follow_redirections(self, request):
        """Follow all redirections of http response."""
        log.debug(LOG_CHECK, "follow all redirections")
        if self.is_redirect():
            # run plugins for old connection
            self.aggregate.plugin_manager.run_connection_plugins(self)
        kwargs = self.get_request_kwargs()
        response = None
        for response in self.session.resolve_redirects(self.url_connection, request, **kwargs):
            newurl = response.url
            log.debug(LOG_CHECK, "Redirected to %r", newurl)
            self.aliases.append(newurl)
            # XXX on redirect errors this is not printed
            self.add_info(_("Redirected to `%(url)s'.") % {'url': newurl})
            self.urlparts = strformat.url_unicode_split(newurl)
            self.build_url_parts()
            self.url_connection = response
            self.headers = response.headers
            self.url = urlutil.urlunsplit(self.urlparts)
            self.scheme = self.urlparts[0].lower()
            self._add_ssl_info()
            self._add_response_info()
            if self.is_redirect():
                # run plugins for old connection
                self.aggregate.plugin_manager.run_connection_plugins(self)

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

    def parse_header_links(self):
        """Parse Link: header URLs."""
        for linktype, linkinfo in self.url_connection.links.items():
            url = linkinfo["url"]
            name = u"Link: header %s" % linktype
            self.add_url(url, name=name)

    def is_parseable (self):
        """
        Check if content is parseable for recursion.

        @return: True if content is parseable
        @rtype: bool
        """
        if not self.valid:
            return False
        # some content types must be validated with the page content
        if self.content_type in ("application/xml", "text/xml"):
            rtype = fileutil.guess_mimetype_read(self.get_content)
            if rtype is not None:
                # XXX side effect
                self.content_type = rtype
        if self.content_type not in self.ContentMimetypes:
            log.debug(LOG_CHECK, "URL with content type %r is not parseable", self.content_type)
            return False
        return True

    def get_robots_txt_url (self):
        """
        Get the according robots.txt URL for this URL.

        @return: robots.txt URL
        @rtype: string
        """
        return "%s://%s/robots.txt" % tuple(self.urlparts[0:2])
