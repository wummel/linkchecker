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
import gzip
import socket
import cStringIO as StringIO
import Cookie

import linkcheck
import linkcheck.url
import linkcheck.robotparser2
import linkcheck.httplib2
import urlbase
import proxysupport

supportHttps = hasattr(linkcheck.httplib2, "HTTPSConnection") and \
               hasattr(socket, "ssl")

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

# Amazon blocks all HEAD requests
_is_amazon = re.compile(r'^www\.amazon\.(com|de|ca|fr|co\.(uk|jp))').search

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
        return has_header_value(headers, 'Connection', 'Close')
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


class HttpUrl (urlbase.UrlBase, proxysupport.ProxySupport):
    """
    Url link with http scheme.
    """

    def __init__ (self, base_url, recursion_level, consumer,
                  parent_url=None, base_ref=None, line=0, column=0, name=u""):
        """
        Initialize basic url data and HTTP specific variables.
        """
        super(HttpUrl, self).__init__(base_url, recursion_level, consumer,
               parent_url=parent_url, base_ref=base_ref, line=line,
               column=column, name=name)
        self.aliases = []
        self.max_redirects = 5
        self.has301status = False
        self.no_anchor = False # remove anchor in request url
        self.persistent = False

    def build_url (self):
        """
        Call super.build_url() and add a missing trailing slash to
        the URL if the URL path is empty.
        """
        super(HttpUrl, self).build_url()
        # encode userinfo
        # XXX
        # check for empty paths
        if not self.urlparts[2]:
            self.add_warning(_("URL path is empty, assuming '/' as path."))
            self.urlparts[2] = '/'
            self.url = urlparse.urlunsplit(self.urlparts)

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
        return self.consumer.cache.robots_txt_allows_url(roboturl, url,
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

        The individual values of the numeric status codes defined for
        HTTP/1.0, and an example set of corresponding Reason-Phrase's, are
        presented below. The reason phrases listed here are only recommended
        -- they may be replaced by local equivalents without affecting the
        protocol. These codes are fully defined in Section 9.
        Status-Code    = "200"   ; OK
        | "201"   ; Created
        | "202"   ; Accepted
        | "204"   ; No Content
        | "301"   ; Moved Permanently
        | "302"   ; Moved Temporarily
        | "304"   ; Not Modified
        | "305"   ; Use Proxy
        | "400"   ; Bad Request
        | "401"   ; Unauthorized
        | "403"   ; Forbidden
        | "404"   ; Not Found
        | "405"   ; Method not allowed
        | "407"   ; Proxy Authentication Required
        | "500"   ; Internal Server Error
        | "501"   ; Not Implemented
        | "502"   ; Bad Gateway
        | "503"   ; Service Unavailable
        | extension-code
        """
        # set the proxy, so a 407 status after this is an error
        self.set_proxy(self.consumer.config["proxy"].get(self.scheme))
        if self.proxy:
            self.add_info(_("Using Proxy %r.") % self.proxy)
        self.headers = None
        self.auth = None
        self.cookies = []
        if not self.allows_robots(self.url):
            self.add_warning(
                       _("Access denied by robots.txt, checked only syntax."))
            return

        if _is_amazon(self.urlparts[1]):
            self.add_warning(_("Amazon servers block HTTP HEAD requests, "
                               "using GET instead."))
            self.method = "GET"
        else:
            # first try with HEAD
            self.method = "HEAD"
        # flag if second try should be done with GET
        fallback_GET = False
        while True:
            try:
                response = self._get_http_response()
            except linkcheck.httplib2.BadStatusLine:
                # some servers send empty HEAD replies
                if self.method == "HEAD":
                    self.method = "GET"
                    #redirect_cache = [self.url]
                    fallback_GET = True
                    continue
                raise
            self.headers = response.msg
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Response: %s %s",
                                response.status, response.reason)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Headers: %s",
                                self.headers)
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                self.set_proxy(self.headers.getheader("Location"))
                self.add_info(_("Enforced Proxy %r.") % self.proxy)
                response = self._get_http_response()
                self.headers = response.msg
                self.proxy, self.proxyauth = oldproxy
            try:
                tries, response = self.follow_redirections(response)
            except linkcheck.httplib2.BadStatusLine:
                # some servers send empty HEAD replies
                if self.method == "HEAD":
                    self.method = "GET"
                    # reset aliases
                    self.aliases = []
                    fallback_GET = True
                    continue
                raise
            if tries == -1:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "already handled")
                return
            if tries >= self.max_redirects:
                if self.method == "HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    self.method = "GET"
                    # reset aliases
                    self.aliases = []
                    fallback_GET = True
                    continue
                self.set_result(_("more than %d redirections, aborting") % \
                                self.max_redirects, valid=False)
                return
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
                if self.method == "HEAD":
                    # fall back to GET
                    self.method = "GET"
                    # reset aliases
                    self.aliases = []
                    fallback_GET = True
                    continue
            elif self.headers and self.method != "GET":
                # test for HEAD support
                mime = self.headers.gettype()
                poweredby = self.headers.get('X-Powered-By', '')
                server = self.headers.get('Server', '')
                if mime == 'application/octet-stream' and \
                   (poweredby.startswith('Zope') or \
                    server.startswith('Zope')):
                    self.add_warning(_("Zope Server cannot determine"
                                " MIME type with HEAD, falling back to GET."))
                    self.method = "GET"
                    continue
            break
        # check url warnings
        effectiveurl = urlparse.urlunsplit(self.urlparts)
        if self.url != effectiveurl:
            self.add_warning(_("Effective URL %s.") % effectiveurl)
            self.url = effectiveurl
        # check response
        self.check_response(response, fallback_GET)

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
            if not isinstance(newurl, unicode):
                newurl = unicode(newurl, "iso8859-1", "ignore")
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Redirected to %r",
                                newurl)
            self.add_info(_("Redirected to %(url)s.") % {'url': newurl})
            redirected, is_idn = linkcheck.url.url_norm(newurl)
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Norm redirected to %r",
                                redirected)
            # check extern filter again
            self.extern = self._get_extern(redirected)
            if self.is_extern():
                self.add_info(
                          _("Outside of domain filter, checked only syntax."))
                return -1, response
            # check robots.txt allowance again
            if not self.allows_robots(redirected):
                self.add_warning(
                       _("Access denied by robots.txt, checked only syntax."))
                return -1, response
            # see about recursive redirect
            all_seen = self.aliases + [self.cache_url_key]
            if redirected in all_seen:
                if self.method == "HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    # fall back to the original url and use GET
                    return self.max_redirects, response
                self.set_result(
                          _("recursive redirection encountered:\n %s") % \
                            "\n  => ".join(all_seen), valid=False)
                return -1, response
            # remember redireced url as alias
            self.aliases.append(redirected)
            # note: urlparts has to be a list
            self.urlparts = linkcheck.url.url_unicode_split(redirected)
            if response.status == 301:
                if not self.has301status:
                    self.add_warning(
                           _("HTTP 301 (moved permanent) encountered: you"
                             " should update this link."))
                    if not (self.url.endswith('/') or \
                       self.url.endswith('.html')):
                        self.add_warning(
                       _("A HTTP 301 redirection occured and the URL has no "
                     "trailing / at the end. All URLs which point to (home) "
                     "directories should end with a / to avoid redirection."))
                    self.has301status = True
            # check cache again on the changed URL
            if self.consumer.cache.checked_redirect(redirected, self):
                return -1, response
            # check if we still have a http url, it could be another
            # scheme, eg https or news
            if self.urlparts[0] != "http":
                self.add_warning(
                           _("HTTP redirection to non-http url encountered; "
                             "the original url was %r.") % self.url)
                # make new Url object
                newobj = linkcheck.checker.get_url_from(
                          redirected, self.recursion_level, self.consumer,
                          parent_url=self.parent_url, base_ref=self.base_ref,
                          line=self.line, column=self.column, name=self.name)
                newobj.warning = self.warning
                newobj.info = self.info
                # append new object to queue
                self.consumer.append_url(newobj)
                # pretend to be finished and logged
                return -1, response
            # new response data
            response = self._get_http_response()
            self.headers = response.msg
            tries += 1
        return tries, response

    def check_response (self, response, fallback_GET):
        """
        Check final result and log it.
        """
        if response.status >= 400:
            self.set_result("%r %s" % (response.status, response.reason),
                            valid=False)
        else:
            if self.headers and self.headers.has_key("Server"):
                server = self.headers['Server']
            else:
                server = _("unknown")
            if fallback_GET:
                self.add_warning(_("Server %r did not support HEAD request,"\
                                   " used GET for checking.") % server)
            if self.no_anchor:
                self.add_warning(_("Server %r had no anchor support, removed"\
                                   " anchor from request.") % server)
            if response.status == 204:
                # no content
                self.add_warning(response.reason)
            # store cookies for valid links
            if self.consumer.config['cookies']:
                for c in self.cookies:
                    self.add_info("Cookie: %s." % c)
                try:
                    out = self.consumer.cache.store_cookies(self.headers,
                                                            self.urlparts[1])
                    for h in out:
                        self.add_info(h)
                except Cookie.CookieError, msg:
                    self.add_warning(_("Could not store cookies: %(msg)s.") %
                                     {'msg': str(msg)})
            if response.status >= 200:
                self.set_result("%r %s" % (response.status, response.reason))
            else:
                self.set_result("OK")
        modified = self.headers.get('Last-Modified', '')
        if modified:
            self.add_info(_("Last modified %s.") % modified)

    def _get_http_response (self):
        """
        Put request and return (status code, status text, mime object).
        Host can be host:port format.
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
        self.url_connection.putrequest(self.method, path, skip_host=True)
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
        if self.consumer.config['cookies']:
            self.cookies = self.consumer.cache.get_cookies(self.urlparts[1],
                                                           self.urlparts[2])
            for c in self.cookies:
                self.url_connection.putheader("Cookie", c)
        self.url_connection.endheaders()
        response = self.url_connection.getresponse()
        self.persistent = http_persistent(response)
        self.timeout = http_timeout(response)
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
        conn = self.consumer.cache.get_connection(key)
        if conn is not None:
            # reuse cached HTTP(S) connection
            return conn
        if scheme == "http":
            h = linkcheck.httplib2.HTTPConnection(host)
        elif scheme == "https" and supportHttps:
            h = linkcheck.httplib2.HTTPSConnection(host)
        else:
            raise linkcheck.LinkCheckerError(
                                 _("Unsupported HTTP url scheme %r") % scheme)
        if self.consumer.config.get("debug"):
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
            encoding = self.headers.get("Content-Encoding")
            if encoding in _supported_encodings:
                try:
                    if encoding == 'deflate':
                        f = StringIO.StringIO(zlib.decompress(self.data))
                    else:
                        f = gzip.GzipFile('', 'rb', 9,
                                          StringIO.StringIO(self.data))
                except zlib.error:
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
        if self.headers.gettype()[:9] != "text/html":
            return False
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding != 'identity':
            self.add_warning(_('Unsupported content encoding %r.') % encoding)
            return False
        return True

    def is_http (self):
        """
        This is a HTTP file.

        @return: True
        @rtype: bool
        """
        return True

    def get_content_type (self):
        """
        Get the MIME type from the Content-Type header value, or
        'application/octet-stream' if not found.

        @return: MIME type
        @rtype: string
        """
        ptype = self.headers.get('Content-Type', 'application/octet-stream')
        if ";" in ptype:
            ptype = ptype.split(';')[0]
        return ptype

    def is_parseable (self):
        """
        Check if content is parseable for recursion.

        @return: True if content is parseable
        @rtype: bool
        """
        if not (self.valid and self.headers):
            return False
        if self.get_content_type() not in ("text/html", "text/css"):
            return False
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding != 'identity':
            self.add_warning(_('Unsupported content encoding %r.') % encoding)
            return False
        return True

    def parse_url (self):
        """
        Parse file contents for new links to check.
        """
        ptype = self.get_content_type()
        if ptype == "text/html":
            self.parse_html()
        elif ptype == "text/css":
            self.parse_css()
        return None

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
        cache_add = self.consumer.cache.add_connection
        if not self.persistent or \
           not cache_add(key, self.url_connection, self.timeout):
            try:
                self.url_connection.close()
            except:
                # ignore close errors
                pass
        self.url_connection = None
