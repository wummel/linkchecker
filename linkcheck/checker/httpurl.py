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

import urlparse
import os
import errno
import zlib
import socket
import rfc822
import time
from cStringIO import StringIO
from datetime import datetime

from .. import (log, LOG_CHECK, gzip2 as gzip, strformat, url as urlutil,
    httplib2 as httplib, LinkCheckerError, httputil, configuration)
from . import (internpaturl, proxysupport, httpheaders as headers, urlbase,
    get_url_from, pooledconnection)
# import warnings
from .const import WARN_HTTP_ROBOTS_DENIED, \
    WARN_HTTP_MOVED_PERMANENT, \
    WARN_HTTP_EMPTY_CONTENT, WARN_HTTP_COOKIE_STORE_ERROR, \
    WARN_HTTP_DECOMPRESS_ERROR, WARN_HTTP_UNSUPPORTED_ENCODING, \
    WARN_HTTP_AUTH_UNKNOWN, WARN_HTTP_AUTH_UNAUTHORIZED

# assumed HTTP header encoding
HEADER_ENCODING = "iso-8859-1"
HTTP_SCHEMAS = ('http://', 'https://')

# helper alias
unicode_safe = strformat.unicode_safe

supportHttps = hasattr(httplib, "HTTPSConnection")

SUPPORTED_ENCODINGS = ('x-gzip', 'gzip', 'deflate')
# Accept-Encoding header value
ACCEPT_ENCODING = ",".join(SUPPORTED_ENCODINGS)
# Accept-Charset header value
ACCEPT_CHARSET = "utf-8,ISO-8859-1;q=0.7,*;q=0.3"
# Accept mime type header value
ACCEPT = "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


class HttpUrl (internpaturl.InternPatternUrl, proxysupport.ProxySupport, pooledconnection.PooledConnection):
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
        # flag if connection is persistent
        self.persistent = False
        # URLs seen through 301/302 redirections
        self.aliases = []
        # initialize check data
        self.headers = None
        self.auth = None
        self.cookies = []
        # temporary data filled when reading redirections
        self._data = None
        # flag telling if GET method is allowed; determined by robots.txt
        self.method_get_allowed = True
        # HttpResponse object
        self.response = None

    def allows_robots (self, url):
        """
        Fetch and parse the robots.txt of given url. Checks if LinkChecker
        can get the requested resource content. HEAD requests however are
        still allowed.

        @param url: the url to be requested
        @type url: string
        @return: True if access is granted, otherwise False
        @rtype: bool
        """
        roboturl = self.get_robots_txt_url()
        user, password = self.get_user_password()
        rb = self.aggregate.robots_txt
        callback = self.aggregate.connections.host_wait
        return rb.allows_url(roboturl, url, self.proxy, user, password,
            callback=callback)

    def add_size_info (self):
        """Get size of URL content from HTTP header."""
        if self.headers and "Content-Length" in self.headers and \
           "Transfer-Encoding" not in self.headers:
            # Note that content-encoding causes size differences since
            # the content data is always decoded.
            try:
                self.size = int(self.getheader("Content-Length"))
                if self.dlsize == -1:
                    self.dlsize = self.size
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
        # set the proxy, so a 407 status after this is an error
        self.set_proxy(self.aggregate.config["proxy"].get(self.scheme))
        self.construct_auth()
        # check robots.txt
        if not self.allows_robots(self.url):
            # remove all previously stored results
            self.add_warning(
                 _("Access denied by robots.txt, skipping content checks."),
                 tag=WARN_HTTP_ROBOTS_DENIED)
            self.method_get_allowed = False
        # first try with HEAD
        self.method = "HEAD"
        # check the http connection
        self.check_http_connection()
        # redirections might have changed the URL
        self.url = urlutil.urlunsplit(self.urlparts)
        # check response
        if self.response is not None:
            self.check_response()
            self.close_response()

    def check_http_connection (self):
        """
        Check HTTP connection and return get response and a flag
        if the check algorithm had to fall back to the GET method.

        @return: response or None if url is already handled
        @rtype: HttpResponse or None
        """
        while True:
            # XXX refactor this
            self.close_response()
            try:
                self._try_http_response()
            except httplib.BadStatusLine as msg:
                # some servers send empty HEAD replies
                if self.method == "HEAD" and self.method_get_allowed:
                    log.debug(LOG_CHECK, "Bad status line %r: falling back to GET", msg)
                    self.fallback_to_get()
                    continue
                raise
            except socket.error as msg:
                # some servers reset the connection on HEAD requests
                if self.method == "HEAD" and self.method_get_allowed and \
                   msg[0] == errno.ECONNRESET:
                    self.fallback_to_get()
                    continue
                raise

            uheaders = unicode_safe(self.headers, encoding=HEADER_ENCODING)
            log.debug(LOG_CHECK, "Headers: %s", uheaders)
            # proxy enforcement (overrides standard proxy)
            if self.response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                newproxy = self.getheader("Location")
                if newproxy:
                    self.add_info(_("Enforced proxy `%(name)s'.") %
                                  {"name": newproxy})
                self.set_proxy(newproxy)
                self.close_response()
                if self.proxy is None:
                    self.set_result(
                         _("Missing 'Location' header with enforced proxy status 305, aborting."),
                         valid=False)
                    return
                elif not self.proxy:
                    self.set_result(
                         _("Empty 'Location' header value with enforced proxy status 305, aborting."),
                         valid=False)
                    return
                self._try_http_response()
                # restore old proxy settings
                self.proxy, self.proxyauth = oldproxy
            try:
                tries = self.follow_redirections()
            except httplib.BadStatusLine as msg:
                # some servers send empty HEAD replies
                if self.method == "HEAD" and self.method_get_allowed:
                    log.debug(LOG_CHECK, "Bad status line %r: falling back to GET", msg)
                    self.fallback_to_get()
                    continue
                raise
            if tries == -1:
                log.debug(LOG_CHECK, "already handled")
                self.close_response()
                self.do_check_content = False
                return
            if tries >= self.max_redirects:
                if self.method == "HEAD" and self.method_get_allowed:
                    # Microsoft servers tend to recurse HEAD requests
                    self.fallback_to_get()
                    continue
                self.set_result(_("more than %d redirections, aborting") %
                                self.max_redirects, valid=False)
                self.close_response()
                self.do_check_content = False
                return
            if self.do_fallback(self.response.status):
                self.fallback_to_get()
                continue
            # user authentication
            if self.response.status == 401:
                authenticate = self.getheader('WWW-Authenticate')
                if authenticate is None:
                    # Either the server intentionally blocked this request,
                    # or there is a form on this page which requires
                    # manual user/password input.
                    # Either way, this is a warning.
                    self.add_warning(_("Unauthorized access without HTTP authentication."),
                       tag=WARN_HTTP_AUTH_UNAUTHORIZED)
                    return
                if not authenticate.startswith("Basic"):
                    # LinkChecker only supports Basic authorization
                    args = {"auth": authenticate}
                    self.add_warning(
                       _("Unsupported HTTP authentication `%(auth)s', " \
                         "only `Basic' authentication is supported.") % args,
                       tag=WARN_HTTP_AUTH_UNKNOWN)
                    return
                if not self.auth:
                    self.construct_auth()
                    if self.auth:
                        continue
            break

    def do_fallback(self, status):
        """Check for fallback according to response status.
        @param status: The HTTP response status
        @ptype status: int
        @return: True if checker should use GET, else False
        @rtype: bool
        """
        if self.method == "HEAD":
            # Some sites do not support HEAD requests, for example
            # youtube sends a 404 with HEAD, 200 with GET. Doh.
            # A 405 "Method not allowed" status should also use GET.
            if status >= 400:
                log.debug(LOG_CHECK, "Method HEAD error %d, falling back to GET", status)
                return True
            # Other sites send 200 with HEAD, but 404 with GET. Bummer.
            poweredby = self.getheader('X-Powered-By', u'')
            server = self.getheader('Server', u'')
            # Some servers (Zope, Apache Coyote/Tomcat, IIS have wrong
            # content type with HEAD. This seems to be a common problem.
            if (poweredby.startswith('Zope') or server.startswith('Zope')
             or server.startswith('Apache-Coyote')
             or ('ASP.NET' in poweredby and 'Microsoft-IIS' in server)):
                return True
        return False

    def fallback_to_get(self):
        """Set method to GET and clear aliases."""
        self.close_response()
        self.close_connection()
        self.method = "GET"
        self.aliases = []
        self.urlparts = strformat.url_unicode_split(self.url)
        self.build_url_parts()

    def construct_auth (self):
        """Construct HTTP Basic authentication credentials if there
        is user/password information available. Does not overwrite if
        credentials have already been constructed."""
        if self.auth:
            return
        _user, _password = self.get_user_password()
        if _user is not None and _password is not None:
            credentials = httputil.encode_base64("%s:%s" % (_user, _password))
            self.auth = "Basic " + credentials
            log.debug(LOG_CHECK, "Using basic authentication")

    def get_content_type (self):
        """Return content MIME type or empty string."""
        if self.content_type is None:
            if self.headers:
                self.content_type = headers.get_content_type(self.headers)
            else:
                self.content_type = u""
        return self.content_type

    def follow_redirections (self, set_result=True):
        """Follow all redirections of http response."""
        log.debug(LOG_CHECK, "follow all redirections")
        redirected = self.url
        tries = 0
        while self.response.status in [301, 302] and self.headers and \
              tries < self.max_redirects:
            num = self.follow_redirection(set_result, redirected)
            if num == -1:
                return num
            redirected = urlutil.urlunsplit(self.urlparts)
            tries += num
        return tries

    def follow_redirection (self, set_result, redirected):
        """Follow one redirection of http response."""
        newurl = self.getheader("Location",
                     self.getheader("Uri", u""))
        # make new url absolute and unicode
        newurl = urlparse.urljoin(redirected, unicode_safe(newurl))
        log.debug(LOG_CHECK, "Redirected to %r", newurl)
        self.add_info(_("Redirected to `%(url)s'.") % {'url': newurl})
        # norm base url - can raise UnicodeError from url.idna_encode()
        redirected, is_idn = urlbase.url_norm(newurl)
        log.debug(LOG_CHECK, "Norm redirected to %r", redirected)
        urlparts = strformat.url_unicode_split(redirected)
        if not self.check_redirection_scheme(redirected, urlparts, set_result):
            return -1
        if not self.check_redirection_newscheme(redirected, urlparts, set_result):
            return -1
        if not self.check_redirection_domain(redirected, urlparts,
                                             set_result):
            return -1
        if not self.check_redirection_robots(redirected, set_result):
            return -1
        num = self.check_redirection_recursion(redirected, set_result)
        if num != 0:
            return num
        if set_result:
            self.check301status()
        self.close_response()
        self.close_connection()
        # remember redirected url as alias
        self.aliases.append(redirected)
        if self.anchor:
            urlparts[4] = self.anchor
        # note: urlparts has to be a list
        self.urlparts = urlparts
        self.build_url_parts()
        # store cookies from redirect response
        self.store_cookies()
        # new response data
        self._try_http_response()
        return 1

    def check_redirection_scheme (self, redirected, urlparts, set_result):
        """Return True if redirection scheme is ok, else False."""
        if urlparts[0] in ('ftp', 'http', 'https'):
            return True
        # For security reasons do not allow redirects to protocols
        # other than HTTP, HTTPS or FTP.
        if set_result:
            self.add_warning(
              _("Redirection to url `%(newurl)s' is not allowed.") %
              {'newurl': redirected})
            self.set_result(_("syntax OK"))
        return False

    def check_redirection_domain (self, redirected, urlparts, set_result):
        """Return True if redirection domain is ok, else False."""
        # XXX does not support user:pass@netloc format
        if urlparts[1] != self.urlparts[1]:
            # URL domain changed
            if self.recursion_level == 0 and urlparts[0] in ('http', 'https'):
                # Add intern patterns for redirection of URLs given by the
                # user for HTTP schemes.
                self.add_intern_pattern(url=redirected)
                return True
        # check extern filter again
        self.extern = None
        self.set_extern(redirected)
        if self.extern[0] and self.extern[1]:
            if set_result:
                self.check301status()
                self.add_info(_("The redirected URL is outside of the domain "
                              "filter, checked only syntax."))
                self.set_result(_("filtered"))
            return False
        return True

    def check_redirection_robots (self, redirected, set_result):
        """Check robots.txt allowance for redirections. Return True if
        allowed, else False."""
        if self.allows_robots(redirected):
            return True
        if set_result:
            self.add_warning(
               _("Access to redirected URL denied by robots.txt, "
                 "checked only syntax."), tag=WARN_HTTP_ROBOTS_DENIED)
            self.set_result(_("syntax OK"))
        return False

    def check_redirection_recursion (self, redirected, set_result):
        """Check for recursive redirect. Return zero if no recursion
        detected, max_redirects for recursion with HEAD request,
        -1 otherwise."""
        all_seen = [self.cache_url_key] + self.aliases
        if redirected not in all_seen:
            return 0
        if self.method == "HEAD" and self.method_get_allowed:
            # Microsoft servers tend to recurse HEAD requests
            # fall back to the original url and use GET
            return self.max_redirects
        if set_result:
            urls = "\n  => ".join(all_seen + [redirected])
            self.set_result(_("recursive redirection encountered:\n %(urls)s") %
                            {"urls": urls}, valid=False)
        return -1

    def check_redirection_newscheme (self, redirected, urlparts, set_result):
        """Check for HTTP(S)/FTP redirection. Return True for
        redirection with same scheme, else False."""
        if urlparts[0] != self.urlparts[0]:
            # changed scheme
            newobj = get_url_from(
                  redirected, self.recursion_level, self.aggregate,
                  parent_url=self.parent_url, base_ref=self.base_ref,
                  line=self.line, column=self.column, name=self.name)
            if set_result:
                self.set_result(_("syntax OK"))
                # append new object to queue
                self.aggregate.urlqueue.put(newobj)
                return False
            raise LinkCheckerError(_('Cannot redirect to different scheme without result'))
        return True

    def check301status (self):
        """If response page has been permanently moved add a warning."""
        if self.response.status == 301 and not self.has301status:
            self.add_warning(_("HTTP 301 (moved permanent) encountered: you"
                               " should update this link."),
                             tag=WARN_HTTP_MOVED_PERMANENT)
            self.has301status = True

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
        if self.response.status >= 400:
            self.set_result(u"%r %s" % (self.response.status, self.response.reason),
                            valid=False)
        else:
            if self.response.status == 204:
                # no content
                self.add_warning(self.response.reason,
                                 tag=WARN_HTTP_EMPTY_CONTENT)
            # store cookies for valid links
            self.store_cookies()
            if self.response.status >= 200:
                self.set_result(u"%r %s" % (self.response.status, self.response.reason))
            else:
                self.set_result(_("OK"))
        modified = rfc822.parsedate(self.getheader('Last-Modified', u''))
        if modified:
            self.modified = datetime.utcfromtimestamp(time.mktime(modified))

    def _try_http_response (self):
        """Try to get a HTTP response object. For persistent
        connections that the server closed unexpected, a new connection
        will be opened.
        """
        try:
            self._get_http_response()
        except socket.error as msg:
            if msg.args[0] == 32 and self.persistent:
                # server closed persistent connection - retry
                log.debug(LOG_CHECK, "Server closed connection: retry")
                self.persistent = False
                self._get_http_response()
            else:
                raise
        except httplib.BadStatusLine as msg:
            if self.persistent:
                # server closed connection - retry
                log.debug(LOG_CHECK, "Empty status line: retry")
                self.persistent = False
                self._get_http_response()
            else:
                raise

    def _get_http_response (self):
        """Send HTTP request and get response object."""
        scheme, host, port = self.get_netloc()
        log.debug(LOG_CHECK, "Connecting to %r", host)
        self.get_http_object(scheme, host, port)
        self.add_connection_request()
        self.add_connection_headers()
        self.response = self.url_connection.getresponse(buffering=True)
        self.headers = self.response.msg
        self.content_type = None
        self.persistent = not self.response.will_close
        if self.persistent and self.method == "HEAD":
            # Some servers send page content after a HEAD request,
            # but only after making the *next* request. This breaks
            # protocol synchronisation. Workaround here is to close
            # the connection after HEAD.
            # Example: http://www.empleo.gob.mx (Apache/1.3.33 (Unix) mod_jk)
            self.persistent = False
        # Note that for POST method the connection should also be closed,
        # but this method is never used.
        # If possible, use official W3C HTTP response name
        if self.response.status in httplib.responses:
            self.response.reason = httplib.responses[self.response.status]
        if self.response.reason:
            self.response.reason = unicode_safe(self.response.reason)
        log.debug(LOG_CHECK, "Response: %s %s", self.response.status, self.response.reason)

    def add_connection_request(self):
        """Add connection request."""
        # the anchor fragment is not part of a HTTP URL, see
        # http://tools.ietf.org/html/rfc2616#section-3.2.2
        anchor = ''
        if self.proxy:
            path = urlutil.urlunsplit((self.urlparts[0], self.urlparts[1],
                                 self.urlparts[2], self.urlparts[3], anchor))
        else:
            path = urlutil.urlunsplit(('', '', self.urlparts[2],
                                        self.urlparts[3], anchor))
        self.url_connection.putrequest(self.method, path, skip_host=True,
                                       skip_accept_encoding=True)

    def add_connection_headers(self):
        """Add connection header."""
        # be sure to use the original host as header even for proxies
        self.url_connection.putheader("Host", self.urlparts[1])
        if self.auth:
            # HTTP authorization
            self.url_connection.putheader("Authorization", self.auth)
        if self.proxyauth:
            self.url_connection.putheader("Proxy-Authorization",
                                         self.proxyauth)
        if (self.parent_url and
            self.parent_url.lower().startswith(HTTP_SCHEMAS)):
            self.url_connection.putheader("Referer", self.parent_url)
        self.url_connection.putheader("User-Agent",
            self.aggregate.config["useragent"])
        # prefer compressed content
        self.url_connection.putheader("Accept-Encoding", ACCEPT_ENCODING)
        # prefer UTF-8 encoding
        self.url_connection.putheader("Accept-Charset", ACCEPT_CHARSET)
        # prefer parseable mime types
        self.url_connection.putheader("Accept", ACCEPT)
        # send do-not-track header
        self.url_connection.putheader("DNT", "1")
        if self.aggregate.config['sendcookies']:
            self.send_cookies()
        self.url_connection.endheaders()

    def store_cookies (self):
        """Save cookies from response headers."""
        if self.aggregate.config['storecookies']:
            for c in self.cookies:
                self.add_info(_("Sent Cookie: %(cookie)s.") %
                              {"cookie": c.client_header_value()})
            errors = self.aggregate.cookies.add(self.headers,
                self.urlparts[0], self.urlparts[1], self.urlparts[2])
            if errors:
                self.add_warning(
                  _("Could not store cookies from headers: %(error)s.") %
                   {'error': "\n".join(errors)},
                   tag=WARN_HTTP_COOKIE_STORE_ERROR)

    def send_cookies (self):
        """Add cookie headers to request."""
        scheme = self.urlparts[0]
        host = self.urlparts[1]
        port = urlutil.default_ports.get(scheme, 80)
        host, port = urlutil.splitport(host, port)
        path = self.urlparts[2] or u"/"
        self.cookies = self.aggregate.cookies.get(scheme, host, port, path)
        if not self.cookies:
            return
        # add one cookie header with all cookie data
        # this is limited by maximum header length
        headername = "Cookie"
        headervalue = ""
        max_value_len = headers.MAX_HEADER_BYTES - len(headername) - 2
        for c in self.cookies:
            cookievalue = c.client_header_value()
            if "version" in c.attributes:
                # add separate header for explicit versioned cookie
                if headervalue:
                    self.url_connection.putheader(headername, headervalue)
                self.url_connection.putheader(headername, cookievalue)
                headervalue = ""
                continue
            if headervalue:
                cookievalue = "; " + cookievalue
            if (len(headervalue) + len(cookievalue)) < max_value_len:
                headervalue += cookievalue
            else:
                log.debug(LOG_CHECK, "Discard too-long cookie %r", cookievalue)
        if headervalue:
            log.debug(LOG_CHECK, "Sending cookie header %s:%s", headername, headervalue)
            self.url_connection.putheader(headername, headervalue)

    def get_http_object (self, scheme, host, port):
        """
        Open a HTTP connection.

        @param host: the host to connect to
        @ptype host: string of the form <host>[:<port>]
        @param scheme: 'http' or 'https'
        @ptype scheme: string
        @return: None
        """
        self.close_connection()
        def create_connection(scheme, host, port):
            """Create a new http or https connection."""
            kwargs = dict(port=port, strict=True, timeout=self.aggregate.config["timeout"])
            if scheme == "http":
                h = httplib.HTTPConnection(host, **kwargs)
            elif scheme == "https" and supportHttps:
                devel_dir = os.path.join(configuration.configdata.install_data, "config")
                sslverify = self.aggregate.config["sslverify"]
                if sslverify:
                    if sslverify is not True:
                        kwargs["ca_certs"] = sslverify
                    else:
                        kwargs["ca_certs"] = configuration.get_share_file(devel_dir, 'ca-certificates.crt')
                h = httplib.HTTPSConnection(host, **kwargs)
            else:
                msg = _("Unsupported HTTP url scheme `%(scheme)s'") % {"scheme": scheme}
                raise LinkCheckerError(msg)
            if log.is_debug(LOG_CHECK):
                h.set_debuglevel(1)
            return h
        self.get_pooled_connection(scheme, host, port, create_connection)
        self.url_connection.connect()

    def read_content (self):
        """Get content of the URL target. The content data is cached after
        the first call to this method.

        @return: URL content, decompressed and decoded
        @rtype: string
        """
        assert self.method_get_allowed, 'unallowed content read'
        if self.method != "GET" or self.response is None:
            self.method = "GET"
            self._try_http_response()
            num = self.follow_redirections(set_result=False)
            if not (0 <= num <= self.max_redirects):
                raise LinkCheckerError(_("Redirection error"))
            # Re-read size info, since the GET request result could be different
            # than a former HEAD request.
            self.add_size_info()
        if self.size > self.MaxFilesizeBytes:
            raise LinkCheckerError(_("File size too large"))
        self.charset = headers.get_charset(self.headers)
        return self._read_content()

    def _read_content (self):
        """Read URL contents."""
        data = self.response.read(self.MaxFilesizeBytes+1)
        if len(data) > self.MaxFilesizeBytes:
            raise LinkCheckerError(_("File size too large"))
        dlsize = len(data)
        self.aggregate.add_download_data(self.cache_content_key, data)
        encoding = headers.get_content_encoding(self.headers)
        if encoding in SUPPORTED_ENCODINGS:
            try:
                if encoding == 'deflate':
                    f = StringIO(zlib.decompress(data))
                else:
                    f = gzip.GzipFile('', 'rb', 9, StringIO(data))
            except zlib.error as msg:
                log.debug(LOG_CHECK, "Error %s data of len %d", encoding, len(data))
                self.add_warning(_("Decompress error %(err)s") %
                                 {"err": str(msg)},
                                 tag=WARN_HTTP_DECOMPRESS_ERROR)
                f = StringIO(data)
            try:
                data = f.read()
            finally:
                f.close()
        return data, dlsize

    def encoding_supported (self):
        """Check if page encoding is supported."""
        encoding = headers.get_content_encoding(self.headers)
        if encoding and encoding not in SUPPORTED_ENCODINGS and \
           encoding != 'identity':
            self.add_warning(_("Unsupported content encoding `%(encoding)s'.") %
                             {"encoding": encoding},
                             tag=WARN_HTTP_UNSUPPORTED_ENCODING)
            return False
        return True

    def can_get_content(self):
        """Check if it's allowed to read content."""
        return self.method_get_allowed

    def content_allows_robots (self):
        """Check if it's allowed to read content before execution."""
        if not self.method_get_allowed:
            return False
        return super(HttpUrl, self).content_allows_robots()

    def check_warningregex (self):
        """Check if it's allowed to read content before execution."""
        if self.method_get_allowed:
            super(HttpUrl, self).check_warningregex()

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
        if self.ContentMimetypes.get(mime) != "html":
            return False
        if self.headers:
            return self.encoding_supported()
        return True

    def is_css (self):
        """Return True iff content of this url is CSS stylesheet."""
        if not self.valid:
            return False
        mime = self.get_content_type()
        if self.ContentMimetypes.get(mime) != "css":
            return False
        if self.headers:
            return self.encoding_supported()
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
        ctype = self.get_content_type()
        if ctype not in self.ContentMimetypes:
            log.debug(LOG_CHECK, "URL with content type %r is not parseable", ctype)
            return False
        return self.encoding_supported()

    def parse_url (self):
        """
        Parse file contents for new links to check.
        """
        ctype = self.get_content_type()
        if self.is_html():
            self.parse_html()
        elif self.is_css():
            self.parse_css()
        elif ctype == "application/x-shockwave-flash":
            self.parse_swf()
        elif ctype == "application/msword":
            self.parse_word()
        elif ctype == "text/vnd.wap.wml":
            self.parse_wml()
        self.add_num_url_info()

    def get_robots_txt_url (self):
        """
        Get the according robots.txt URL for this URL.

        @return: robots.txt URL
        @rtype: string
        """
        return "%s://%s/robots.txt" % tuple(self.urlparts[0:2])

    def close_response(self):
        """Close the HTTP response object."""
        if self.response is None:
            return
        self.response.close()
        self.response = None

    def close_connection (self):
        """Release the connection from the connection pool. Persistent
        connections will not be closed.
        """
        log.debug(LOG_CHECK, "Closing %s", self.url_connection)
        if self.url_connection is None:
            # no connection is open
            return
        # add to cached connections
        scheme, host, port = self.get_netloc()
        if self.persistent and self.url_connection.is_idle():
            expiration = time.time() + headers.http_keepalive(self.headers)
        else:
            self.close_response()
            expiration = None
        self.aggregate.connections.release(scheme, host, port, self.url_connection, expiration=expiration)
        self.url_connection = None
