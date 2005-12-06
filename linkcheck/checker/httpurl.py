# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2005  Bastian Kleineidam
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
Handle http links.
"""

import urlparse
import time
import re
import zlib
import socket
import cStringIO as StringIO
import Cookie

import linkcheck
import linkcheck.url
import linkcheck.gzip2
import linkcheck.strformat
import linkcheck.robotparser2
import linkcheck.httplib2
import httpheaders as headers
import internpaturl
import proxysupport

supportHttps = hasattr(linkcheck.httplib2, "HTTPSConnection") and \
               hasattr(socket, "ssl")

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

# Amazon blocks all HEAD requests
_is_amazon = re.compile(r'^www\.amazon\.(com|de|ca|fr|co\.(uk|jp))').search

# Stolen from Python CVS urllib2.py
# Mapping status codes to official W3C names
httpresponses = {
    100: 'Continue',
    101: 'Switching Protocols',

    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: '(Unused)',
    307: 'Temporary Redirect',

    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',

    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
}

class HttpUrl (internpaturl.InternPatternUrl, proxysupport.ProxySupport):
    """
    Url link with http scheme.
    """

    def reset (self):
        """
        Initialize HTTP specific variables.
        """
        super(HttpUrl, self).reset()
        self.max_redirects = 5
        self.has301status = False
        # some servers do not support anchors in requests
        # this flag tells us to remove the anchor in request url
        self.no_anchor = False
        # flag if check had to fallback from HEAD to GET method
        self.fallback_get = False
        # flag if connection is persistent
        self.persistent = False
        # URLs seen through 301/302 redirections
        self.aliases = []

    def allows_robots (self, url):
        """
        Fetch and parse the robots.txt of given url. Checks if LinkChecker
        can access the requested resource.

        @param url: the url to be requested
        @type url: string
        @return: True if access is granted, otherwise False
        @rtype: bool
        """
        roboturl = self.get_robots_txt_url()
        user, password = self.get_user_password()
        return self.consumer.robots_txt_allows_url(roboturl, url,
                                                   user, password)

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
        # set the proxy, so a 407 status after this is an error
        self.set_proxy(self.consumer.config("proxy").get(self.scheme))
        # initialize check data
        self.headers = None
        self.auth = None
        self.cookies = []
        # check robots.txt
        if not self.allows_robots(self.url):
            # remove all previously stored results
            self.add_warning(
                       _("Access denied by robots.txt, checked only syntax."),
                       tag="http-robots-denied")
            self.set_result(u"syntax OK")
            return
        # check for amazon server quirk
        if _is_amazon(self.urlparts[1]):
            self.add_info(_("Amazon servers block HTTP HEAD requests, "
                            "using GET instead."))
            self.method = "GET"
        else:
            # first try with HEAD
            self.method = "HEAD"
        # check the http connection
        response = self.check_http_connection()
        if self.headers and self.headers.has_key("Server"):
            server = self.headers['Server']
        else:
            server = _("unknown")
        if self.fallback_get:
            self.add_info(_("Server %r did not support HEAD request; "\
                            "a GET request was used instead.") % server)
        if self.no_anchor:
            self.add_warning(_("Server %r had no anchor support, removed"\
                               " anchor from request.") % server,
                             tag="http-no-anchor-support")
        # redirections might have changed the URL
        newurl = urlparse.urlunsplit(self.urlparts)
        if self.url != newurl:
            self.url = newurl
        # check response
        if response:
            self.check_response(response)

    def check_http_connection (self):
        """
        Check HTTP connection and return get response and a flag
        if the check algorithm had to fall back to the GET method.

        @return: response or None if url is already handled
        @rtype: HttpResponse or None
        """
        while True:
            try:
                response = self._get_http_response()
            except linkcheck.httplib2.BadStatusLine:
                # some servers send empty HEAD replies
                if self.method == "HEAD":
                    self.method = "GET"
                    self.aliases = []
                    self.fallback_get = True
                    continue
                raise
            if response.reason:
                response.reason = \
                        linkcheck.strformat.unicode_safe(response.reason)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Response: %s %s",
                                response.status, response.reason)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Headers: %s",
                                self.headers)
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                newproxy = self.headers.getheader("Location")
                self.add_info(_("Enforced proxy %r.") % newproxy)
                self.set_proxy(newproxy)
                if not self.proxy:
                    self.set_result(
                         _("Enforced proxy %r ignored, aborting.") % newproxy,
                         valid=False)
                    return response
                response = self._get_http_response()
                # restore old proxy settings
                self.proxy, self.proxyauth = oldproxy
            try:
                tries, response = self.follow_redirections(response)
            except linkcheck.httplib2.BadStatusLine:
                # some servers send empty HEAD replies
                if self.method == "HEAD":
                    self.method = "GET"
                    self.aliases = []
                    self.fallback_get = True
                    continue
                raise
            if tries == -1:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "already handled")
                return None
            if tries >= self.max_redirects:
                if self.method == "HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    self.method = "GET"
                    self.aliases = []
                    self.fallback_get = True
                    continue
                self.set_result(_("more than %d redirections, aborting") % \
                                self.max_redirects, valid=False)
                return response
            # user authentication
            if response.status == 401:
                if not self.auth:
                    import base64
                    _user, _password = self.get_user_password()
                    self.auth = "Basic "+\
                        base64.encodestring("%s:%s" % (_user, _password))
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                                    "Authentication %s/%s", _user, _password)
                    continue
            elif response.status >= 400:
                if self.headers and self.urlparts[4] and not self.no_anchor:
                    self.no_anchor = True
                    continue
                # retry with GET (but do not set fallback flag)
                if self.method == "HEAD":
                    self.method = "GET"
                    self.aliases = []
                    continue
            elif self.headers and self.method == "HEAD":
                # test for HEAD support
                mime = headers.get_content_type(self.headers)
                poweredby = self.headers.get('X-Powered-By', '')
                server = self.headers.get('Server', '')
                if mime == 'application/octet-stream' and \
                  (poweredby.startswith('Zope') or server.startswith('Zope')):
                    # Zope server could not get Content-Type with HEAD
                    self.method = "GET"
                    self.aliases = []
                    self.fallback_get = True
                    continue
            break
        return response

    def follow_redirections (self, response):
        """
        Follow all redirections of http response.
        """
        linkcheck.log.debug(linkcheck.LOG_CHECK, "follow all redirections")
        redirected = self.url
        tries = 0
        while response.status in [301, 302] and self.headers and \
              tries < self.max_redirects:
            newurl = self.headers.getheader("Location",
                         self.headers.getheader("Uri", ""))
            # make new url absolute and unicode
            newurl = urlparse.urljoin(redirected, newurl)
            newurl = linkcheck.strformat.unicode_safe(newurl)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Redirected to %r",
                                newurl)
            self.add_info(_("Redirected to %(url)s.") % {'url': newurl})
            redirected, is_idn = linkcheck.url.url_norm(newurl)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Norm redirected to %r",
                                redirected)
            urlparts = linkcheck.strformat.url_unicode_split(redirected)
            # check if we still have the same scheme type, it could be a
            # different one
            if urlparts[0] != self.scheme:
                self.add_warning(
                           _("Redirection to different URL type encountered; "
                             "the original URL was %r.") % self.url,
                           tag="http-wrong-redirect")
            # check extern filter again
            self.set_extern(redirected)
            if self.extern[0] and self.extern[0]:
                self.add_info(
                          _("The redirected URL is outside of the domain " \
                            "filter, checked only syntax."))
                self.set_result(u"filtered")
                return -1, response
            # check robots.txt allowance again
            if not self.allows_robots(redirected):
                self.add_warning(
                       _("Access to redirected URL denied by robots.txt, " \
                         "checked only syntax."),
                       tag="http-robots-denied")
                self.set_result(u"syntax OK")
                return -1, response
            # see about recursive redirect
            all_seen = [self.cache_url_key] + self.aliases
            if redirected in all_seen:
                if self.method == "HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    # fall back to the original url and use GET
                    return self.max_redirects, response
                recursion = all_seen + [redirected]
                self.set_result(
                          _("recursive redirection encountered:\n %s") % \
                            "\n  => ".join(recursion), valid=False)
                return -1, response
            # remember redireced url as alias
            self.aliases.append(redirected)
            # note: urlparts has to be a list
            self.urlparts = urlparts
            if response.status == 301:
                if not self.has301status:
                    self.add_warning(
                           _("HTTP 301 (moved permanent) encountered: you"
                             " should update this link."),
                           tag="http-moved-permanent")
                    self.has301status = True
            # check cache again on the changed URL
            if self.consumer.checked_redirect(redirected, self):
                return -1, response
            # in case of changed scheme make new URL object
            if self.urlparts[0] != self.scheme:
                newobj = linkcheck.checker.get_url_from(
                          redirected, self.recursion_level, self.consumer,
                          parent_url=self.parent_url, base_ref=self.base_ref,
                          line=self.line, column=self.column, name=self.name,
                          cmdline=False)
                newobj.warnings = self.warnings
                newobj.info = self.info
                # append new object to queue
                self.consumer.append_url(newobj)
                # pretend to be finished and logged
                return -1, response
            # new response data
            response = self._get_http_response()
            tries += 1
        return tries, response

    def check_response (self, response):
        """
        Check final result and log it.
        """
        if response.status >= 400:
            self.set_result(u"%r %s" % (response.status, response.reason),
                            valid=False)
        else:
            if response.status == 204:
                # no content
                self.add_warning(
                            linkcheck.strformat.unicode_safe(response.reason),
                            tag="http-empty-content")
            # store cookies for valid links
            if self.consumer.config('cookies'):
                for c in self.cookies:
                    self.add_info(_("Store cookie: %s.") % c)
                try:
                    out = self.consumer.store_cookies(self.headers,
                                                      self.urlparts[1])
                    for h in out:
                        self.add_info(linkcheck.strformat.unicode_safe(h))
                except Cookie.CookieError, msg:
                    self.add_warning(_("Could not store cookies: %(msg)s.") %
                                     {'msg': str(msg)},
                                     tag="http-cookie-store-error")
            if response.status >= 200:
                self.set_result(u"%r %s" % (response.status, response.reason))
            else:
                self.set_result(u"OK")
        modified = self.headers.get('Last-Modified', '')
        if modified:
            self.add_info(_("Last modified %s.") % modified)

    def _get_http_response (self):
        """
        Send HTTP request and get response object.
        """
        if self.proxy:
            host = self.proxy
            scheme = "http"
        else:
            host = self.urlparts[1]
            scheme = self.urlparts[0]
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Connecting to %r", host)
        if self.url_connection:
            self.close_connection()
        self.url_connection = self.get_http_object(host, scheme)
        if self.no_anchor:
            anchor = ''
        else:
            anchor = self.urlparts[4]
        if self.proxy:
            path = urlparse.urlunsplit((self.urlparts[0], self.urlparts[1],
                                 self.urlparts[2], self.urlparts[3], anchor))
        else:
            path = urlparse.urlunsplit(('', '', self.urlparts[2],
                                        self.urlparts[3], anchor))
        self.url_connection.putrequest(self.method, path, skip_host=True,
                                       skip_accept_encoding=True)
        self.url_connection.putheader("Host", host)
        # userinfo is from http://user@pass:host/
        if self.userinfo:
            self.url_connection.putheader("Authorization", self.userinfo)
        # auth is the -u and -p configuration options
        elif self.auth:
            self.url_connection.putheader("Authorization", self.auth)
        if self.proxyauth:
            self.url_connection.putheader("Proxy-Authorization",
                                         self.proxyauth)
        if self.parent_url and self.parent_url.startswith('http://'):
            self.url_connection.putheader("Referer", self.parent_url)
        self.url_connection.putheader("User-Agent",
                                      linkcheck.configuration.UserAgent)
        self.url_connection.putheader("Accept-Encoding",
                                  "gzip;q=1.0, deflate;q=0.9, identity;q=0.5")
        if self.consumer.config('cookies'):
            self.cookies = self.consumer.get_cookies(self.urlparts[1],
                                                     self.urlparts[2])
            for c in self.cookies:
                self.url_connection.putheader("Cookie", c)
        self.url_connection.endheaders()
        response = self.url_connection.getresponse()
        self.persistent = headers.http_persistent(response)
        self.timeout = headers.http_timeout(response)
        self.headers = response.msg
        # If possible, use official W3C HTTP response name
        if response.status in httpresponses:
            response.reason = httpresponses[response.status]
        return response

    def get_http_object (self, host, scheme):
        """
        Open a HTTP connection.

        @param host: the host to connect to
        @type host: string of the form <host>[:<port>]
        @param scheme: 'http' or 'https'
        @type scheme: string
        @return: open HTTP(S) connection
        @rtype: httplib.HTTP(S)Connection
        """
        _user, _password = self.get_user_password()
        key = (scheme, self.urlparts[1], _user, _password)
        conn = self.consumer.get_connection(key)
        if conn is not None:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "reuse cached HTTP(S) connection %s", conn)
            return conn
        if scheme == "http":
            h = linkcheck.httplib2.HTTPConnection(host)
        elif scheme == "https" and supportHttps:
            h = linkcheck.httplib2.HTTPSConnection(host)
        else:
            raise linkcheck.LinkCheckerError, \
                                 _("Unsupported HTTP url scheme %r") % scheme
        if linkcheck.log.is_debug(linkcheck.LOG_CHECK):
            h.set_debuglevel(1)
        h.connect()
        return h

    def get_content (self):
        """
        Get content of the URL target. The content data is cached after
        the first call to this method.

        @return: URL content, decompressed and decoded
        @rtype: string
        """
        if not self.has_content:
            self.method = "GET"
            self.has_content = True
            self.close_connection()
            t = time.time()
            response = self._get_http_response()
            self.headers = response.msg
            self.data = response.read()
            encoding = headers.get_content_encoding(self.headers)
            if encoding in _supported_encodings:
                try:
                    if encoding == 'deflate':
                        f = StringIO.StringIO(zlib.decompress(self.data))
                    else:
                        f = linkcheck.gzip2.GzipFile('', 'rb', 9,
                                          StringIO.StringIO(self.data))
                except zlib.error, msg:
                    self.add_warning(_("Decompress error %(err)s") % \
                                     {"err": str(msg)},
                                     tag="http-decompress-error")
                    f = StringIO.StringIO(self.data)
                self.data = f.read()
            self.downloadtime = time.time() - t
        return self.data

    def is_html (self):
        """
        See if this URL points to a HTML file by looking at the
        Content-Type header, file extension and file content.

        @return: True if URL points to HTML file
        @rtype: bool
        """
        if not (self.valid and self.headers):
            return False
        if headers.get_content_type(self.headers) != "text/html":
            return False
        encoding = headers.get_content_encoding(self.headers)
        if encoding and encoding not in _supported_encodings and \
           encoding != 'identity':
            self.add_warning(_('Unsupported content encoding %r.') % encoding,
                             tag="http-unsupported-encoding")
            return False
        return True

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
        if not (self.valid and self.headers):
            return False
        if headers.get_content_type(self.headers) not in \
           ("text/html", "text/css"):
            return False
        encoding = headers.get_content_encoding(self.headers)
        if encoding and encoding not in _supported_encodings and \
           encoding != 'identity':
            self.add_warning(_('Unsupported content encoding %r.') % encoding,
                             tag="http-unsupported-encoding")
            return False
        return True

    def parse_url (self):
        """
        Parse file contents for new links to check.
        """
        ptype = headers.get_content_type(self.headers)
        if ptype == "text/html":
            self.parse_html()
        elif ptype == "text/css":
            self.parse_css()

    def get_robots_txt_url (self):
        """
        Get the according robots.txt URL for this URL.

        @return: robots.txt URL
        @rtype: string
        """
        return "%s://%s/robots.txt" % tuple(self.urlparts[0:2])

    def close_connection (self):
        """
        If connection is persistent, add it to the connection pool.
        Else close the connection. Errors on closing are ignored.
        """
        if self.url_connection is None:
            # no connection is open
            return
        # add to cached connections
        _user, _password = self.get_user_password()
        key = ("http", self.urlparts[1], _user, _password)
        cache_add = self.consumer.add_connection
        # note: only cache the connection when it is persistent
        # and all pending content has been received
        if not self.persistent or not self.has_content or \
           not cache_add(key, self.url_connection, self.timeout):
            try:
                self.url_connection.close()
            except:
                # ignore close errors
                pass
        self.url_connection = None
