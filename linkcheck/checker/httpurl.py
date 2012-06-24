# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2012 Bastian Kleineidam
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
import urllib
import os
import re
import errno
import zlib
import socket
from cStringIO import StringIO

from .. import (log, LOG_CHECK, gzip2 as gzip, strformat, url as urlutil,
    httplib2 as httplib, LinkCheckerError, get_link_pat, httputil,
    configuration)
from . import (internpaturl, proxysupport, httpheaders as headers, urlbase,
    get_url_from)
# import warnings
from .const import WARN_HTTP_ROBOTS_DENIED, \
    WARN_HTTP_WRONG_REDIRECT, WARN_HTTP_MOVED_PERMANENT, \
    WARN_HTTP_EMPTY_CONTENT, WARN_HTTP_COOKIE_STORE_ERROR, \
    WARN_HTTP_DECOMPRESS_ERROR, WARN_HTTP_UNSUPPORTED_ENCODING, \
    WARN_HTTP_AUTH_UNKNOWN

# assumed HTTP header encoding
HEADER_ENCODING = "iso-8859-1"

# helper alias
unicode_safe = strformat.unicode_safe

supportHttps = hasattr(httplib, "HTTPSConnection")

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

# Amazon blocks all HEAD requests
_is_amazon = re.compile(r'^www\.amazon\.(com|de|ca|fr|co\.(uk|jp))').search


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
        # flag if check had to fallback from HEAD to GET method
        self.fallback_get = False
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
        # flag indicating connection reuse
        self.reused_connection = False
        # flag telling if GET method is allowed; determined by robots.txt
        self.method_get_allowed = True

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
        # check for amazon server quirk
        if _is_amazon(self.urlparts[1]):
            self.add_info(_("Amazon servers block HTTP HEAD requests."))
            if self.method_get_allowed:
                self.add_info(_("Using GET method for Amazon server."))
                self.method = "GET"
        # check the http connection
        response = self.check_http_connection()
        if self.headers and "Server" in self.headers:
            server = self.getheader('Server')
        else:
            server = _("unknown")
        if self.fallback_get:
            self.add_info(_("Server `%(name)s' did not support HEAD request; "
                            "a GET request was used instead.") %
                            {"name": server})
        # redirections might have changed the URL
        self.url = urlutil.urlunsplit(self.urlparts)
        # check response
        if response:
            self.check_response(response)
            response.close()

    def check_http_connection (self):
        """
        Check HTTP connection and return get response and a flag
        if the check algorithm had to fall back to the GET method.

        @return: response or None if url is already handled
        @rtype: HttpResponse or None
        """
        response = None
        while True:
            if response is not None:
                response.close()
            try:
                response = self._try_http_response()
            except httplib.BadStatusLine, msg:
                # some servers send empty HEAD replies
                if self.method == "HEAD" and self.method_get_allowed:
                    log.debug(LOG_CHECK, "Bad status line %r: falling back to GET", msg)
                    self.fallback_to_get()
                    continue
                raise
            except socket.error, msg:
                # some servers reset the connection on HEAD requests
                if self.method == "HEAD" and self.method_get_allowed and \
                   msg[0] == errno.ECONNRESET:
                    self.fallback_to_get()
                    continue
                raise
            if response.reason:
                response.reason = unicode_safe(response.reason)
            log.debug(LOG_CHECK,
                "Response: %s %s", response.status, response.reason)
            uheaders = unicode_safe(self.headers, encoding=HEADER_ENCODING)
            log.debug(LOG_CHECK, "Headers: %s", uheaders)
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                newproxy = self.getheader("Location")
                self.add_info(_("Enforced proxy `%(name)s'.") %
                              {"name": newproxy})
                self.set_proxy(newproxy)
                if not self.proxy:
                    self.set_result(
                         _("Enforced proxy `%(name)s' ignored, aborting.") %
                         {"name": newproxy},
                         valid=False)
                    return response
                response.close()
                response = self._try_http_response()
                # restore old proxy settings
                self.proxy, self.proxyauth = oldproxy
            try:
                tries, response = self.follow_redirections(response)
            except httplib.BadStatusLine, msg:
                # some servers send empty HEAD replies
                if self.method == "HEAD" and self.method_get_allowed:
                    log.debug(LOG_CHECK, "Bad status line %r: falling back to GET", msg)
                    self.fallback_to_get()
                    continue
                raise
            if tries == -1:
                log.debug(LOG_CHECK, "already handled")
                response.close()
                self.do_check_content = False
                return None
            if tries >= self.max_redirects:
                if self.method == "HEAD" and self.method_get_allowed:
                    # Microsoft servers tend to recurse HEAD requests
                    self.fallback_to_get()
                    continue
                self.set_result(_("more than %d redirections, aborting") %
                                self.max_redirects, valid=False)
                return response
            # user authentication
            if response.status == 401:
                authenticate = self.getheader('WWW-Authenticate')
                if not authenticate or not authenticate.startswith("Basic"):
                    # LinkChecker only supports Basic authorization
                    args = {"auth": authenticate}
                    self.add_warning(
                       _("Unsupported HTTP authentication `%(auth)s', " \
                         "only `Basic' authentication is supported.") % args,
                       tag=WARN_HTTP_AUTH_UNKNOWN)
                    return
                if not self.auth:
                    self.construct_auth()
                    continue
            if (self.headers and self.method == "HEAD" and
                self.method_get_allowed):
                # test for HEAD support
                poweredby = self.getheader('X-Powered-By', u'')
                server = self.getheader('Server', u'')
                if (poweredby.startswith('Zope') or server.startswith('Zope')
                 or ('ASP.NET' in poweredby and 'Microsoft-IIS' in server)):
                    # Zope or IIS server could not get Content-Type with HEAD
                    # http://intermapper.com.dev4.silvertech.net/bogus.aspx
                    self.fallback_to_get()
                    continue
            break
        return response

    def fallback_to_get(self):
        """Set method to GET and set fallback flag."""
        self.method = "GET"
        self.aliases = []
        self.fallback_get = True

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

    def follow_redirections (self, response, set_result=True):
        """Follow all redirections of http response."""
        log.debug(LOG_CHECK, "follow all redirections")
        redirected = self.url
        tries = 0
        while response.status in [301, 302] and self.headers and \
              tries < self.max_redirects:
            num, response = self.follow_redirection(response, set_result, redirected)
            if num == -1:
                return num, response
            redirected = urlutil.urlunsplit(self.urlparts)
            tries += num
        return tries, response

    def follow_redirection (self, response, set_result, redirected):
        """Follow one redirection of http response."""
        newurl = self.getheader("Location",
                     self.getheader("Uri", u""))
        # make new url absolute and unicode
        newurl = urlparse.urljoin(redirected, unicode_safe(newurl))
        log.debug(LOG_CHECK, "Redirected to %r", newurl)
        self.add_info(_("Redirected to `%(url)s'.") % {'url': newurl})
        # norm base url - can raise UnicodeError from url.idna_encode()
        redirected, is_idn = urlbase.url_norm(newurl)
        # XXX recalculate authentication information when available
        log.debug(LOG_CHECK, "Norm redirected to %r", redirected)
        urlparts = strformat.url_unicode_split(redirected)
        if not self.check_redirection_scheme(redirected, urlparts, set_result):
            return -1, response
        if not self.check_redirection_domain(redirected, urlparts,
                                             set_result, response):
            return -1, response
        if not self.check_redirection_robots(redirected, set_result):
            return -1, response
        num = self.check_redirection_recursion(redirected, set_result)
        if num != 0:
            return num, response
        if not self.check_redirection_newscheme (redirected, urlparts, set_result):
            return -1, response
        # remember redirected url as alias
        self.aliases.append(redirected)
        # note: urlparts has to be a list
        self.urlparts = urlparts
        if set_result:
            self.check301status(response)
        # check cache again on the changed URL
        if self.aggregate.urlqueue.checked_redirect(redirected, self):
            return -1, response
        # store cookies from redirect response
        self.store_cookies()
        # new response data
        response.close()
        response = self._try_http_response()
        return 1, response

    def check_redirection_scheme (self, redirected, urlparts, set_result):
        """Return True if redirection scheme is ok, else False."""
        if urlparts[0] in ('ftp', 'http', 'https'):
            return True
        # in case of changed scheme make new URL object
        # For security reasons do not allow redirects to protocols
        # other than HTTP, HTTPS or FTP.
        if set_result:
            self.add_warning(
              _("Redirection to url `%(newurl)s' is not allowed.") %
              {'newurl': redirected})
            self.set_result(u"syntax OK")
        return False

    def check_redirection_domain (self, redirected, urlparts, set_result, response):
        """Return True if redirection domain is ok, else False."""
        # XXX does not support user:pass@netloc format
        if urlparts[1] != self.urlparts[1]:
            # URL domain changed
            if self.recursion_level == 0 and urlparts[0] in ('http', 'https'):
                # Add intern patterns for redirection of URLs given by the
                # user for HTTP schemes.
                pat = internpaturl.get_intern_pattern(redirected)
                log.debug(LOG_CHECK, "Add intern pattern %r", pat)
                self.aggregate.config['internlinks'].append(get_link_pat(pat))
                return True
        # check extern filter again
        self.set_extern(redirected)
        if self.extern[0] and self.extern[1]:
            if set_result:
                self.check301status(response)
                self.add_info(_("The redirected URL is outside of the domain "
                              "filter, checked only syntax."))
                self.set_result(u"filtered")
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
            self.set_result(u"syntax OK")
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
        """Check for HTTP(S)/FTP redirection. Return True for HTTP(S)
        redirection, False for FTP."""
        if urlparts[0] in ('http', 'https'):
            return True
        # ftp scheme
        assert urlparts[0] == 'ftp', 'Invalid redirection %r' % redirected
        newobj = get_url_from(
                  redirected, self.recursion_level, self.aggregate,
                  parent_url=self.parent_url, base_ref=self.base_ref,
                  line=self.line, column=self.column, name=self.name)
        if set_result:
            self.add_warning(
             _("Redirection to URL `%(newurl)s' with different scheme"
               " found; the original URL was `%(url)s'.") %
             {"url": self.url, "newurl": newobj.url},
             tag=WARN_HTTP_WRONG_REDIRECT)
            self.set_result(u"syntax OK")
        # append new object to queue
        self.aggregate.urlqueue.put(newobj)
        return False

    def check301status (self, response):
        """If response page has been permanently moved add a warning."""
        if response.status == 301 and not self.has301status:
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

    def get_alias_cache_data (self):
        """
        Return all data values that should be put in the cache,
        minus redirection warnings.
        """
        data = self.get_cache_data()
        data["warnings"] = [
            x for x in self.warnings if x[0] != WARN_HTTP_MOVED_PERMANENT]
        data["info"] = self.info
        return data

    def check_response (self, response):
        """Check final result and log it."""
        if response.status >= 400:
            self.set_result(u"%r %s" % (response.status, response.reason),
                            valid=False)
        else:
            if response.status == 204:
                # no content
                self.add_warning(unicode_safe(response.reason),
                                 tag=WARN_HTTP_EMPTY_CONTENT)
            # store cookies for valid links
            self.store_cookies()
            if response.status >= 200:
                self.set_result(u"%r %s" % (response.status, response.reason))
            else:
                self.set_result(u"OK")
        modified = self.getheader('Last-Modified', u'')
        if modified:
            self.add_info(_("Last modified %(date)s.") % {"date": modified})

    def _try_http_response (self):
        """Try to get a HTTP response object. For reused persistent
        connections that the server closed unexpected, a new connection
        will be opened.
        """
        try:
            return self._get_http_response()
        except socket.error, msg:
            if msg.args[0] == 32 and self.reused_connection:
                # server closed persistent connection - retry
                log.debug(LOG_CHECK, "Server closed connection: retry")
                self.persistent = False
                return self._get_http_response()
            raise
        except httplib.BadStatusLine, msg:
            if not msg and self.reused_connection:
                # server closed connection - retry
                log.debug(LOG_CHECK, "Empty status line: retry")
                self.persistent = False
                return self._get_http_response()
            raise

    def _get_http_response (self):
        """
        Send HTTP request and get response object.
        """
        if self.proxy:
            scheme = self.proxytype
            host = self.proxy
        else:
            scheme = self.urlparts[0]
            host = self.urlparts[1]
        log.debug(LOG_CHECK, "Connecting to %r", host)
        # close/release a previous connection
        self.close_connection()
        self.url_connection = self.get_http_object(host, scheme)
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
        # be sure to use the original host as header even for proxies
        self.url_connection.putheader("Host", self.urlparts[1])
        if self.auth:
            # HTTP authorization
            self.url_connection.putheader("Authorization", self.auth)
        if self.proxyauth:
            self.url_connection.putheader("Proxy-Authorization",
                                         self.proxyauth)
        if (self.parent_url and
            self.parent_url.startswith(('http://', 'https://'))):
            self.url_connection.putheader("Referer", self.parent_url)
        self.url_connection.putheader("User-Agent",
            self.aggregate.config["useragent"])
        self.url_connection.putheader("Accept-Encoding",
                                  "gzip;q=1.0, deflate;q=0.9, identity;q=0.5")
        if self.aggregate.config['sendcookies']:
            self.send_cookies()
        self.url_connection.endheaders()
        response = self.url_connection.getresponse(True)
        self.timeout = headers.http_timeout(response)
        self.headers = response.msg
        self.content_type = None
        self.persistent = not response.will_close
        if self.persistent and self.method == "HEAD":
            # Some servers send page content after a HEAD request,
            # but only after making the *next* request. This breaks
            # protocol synchronisation. Workaround here is to close
            # the connection after HEAD.
            # Example: http://www.empleo.gob.mx (Apache/1.3.33 (Unix) mod_jk)
            self.persistent = False
        # Note that for POST method the connection should also be closed,
        # but this method is never used.
        if self.persistent and (self.method == "GET" or
           self.getheader("Content-Length") != u"0"):
            # always read content from persistent connections
            self._read_content(response)
            assert not response.will_close
        # If possible, use official W3C HTTP response name
        if response.status in httplib.responses:
            response.reason = httplib.responses[response.status]
        return response

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
        host, port = urllib.splitnport(host, port)
        path = self.urlparts[2]
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
            self.url_connection.putheader(headername, headervalue)

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
        key = self.get_connection_key(scheme, host)
        conn = self.aggregate.connections.get(key)
        if conn is not None:
            log.debug(LOG_CHECK, "reuse cached HTTP(S) connection %s", conn)
            self.reused_connection = True
            return conn
        self.aggregate.connections.wait_for_host(host)
        if scheme == "http":
            h = httplib.HTTPConnection(host)
        elif scheme == "https" and supportHttps:
            devel_dir = os.path.join(configuration.configdata.install_data, "config")
            ca_certs = configuration.get_share_file(devel_dir, 'ca-certificates.crt')
            h = httplib.HTTPSConnection(host, ca_certs=ca_certs)
        else:
            msg = _("Unsupported HTTP url scheme `%(scheme)s'") % {"scheme": scheme}
            raise LinkCheckerError(msg)
        if log.is_debug(LOG_CHECK):
            h.set_debuglevel(1)
        h.connect()
        return h

    def read_content (self):
        """Get content of the URL target. The content data is cached after
        the first call to this method.

        @return: URL content, decompressed and decoded
        @rtype: string
        """
        assert self.method_get_allowed, 'unallowed content read'
        self.method = "GET"
        response = self._try_http_response()
        response = self.follow_redirections(response, set_result=False)[1]
        self.headers = response.msg
        self.content_type = None
        self.charset = headers.get_charset(self.headers)
        # Re-read size info, since the GET request result could be different
        # than a former HEAD request.
        self.add_size_info()
        if self._data is None:
            if self.size > self.MaxFilesizeBytes:
                raise LinkCheckerError(_("File size too large"))
            self._read_content(response)
        data, size = self._data, self._size
        self._data = self._size = None
        return data, size

    def _read_content (self, response):
        """Read URL contents and store then in self._data.
        This way, the method can be called by other functions than
        read_content()"""
        data = response.read()
        self._size = len(data)
        encoding = headers.get_content_encoding(self.headers)
        if encoding in _supported_encodings:
            try:
                if encoding == 'deflate':
                    f = StringIO(zlib.decompress(data))
                else:
                    f = gzip.GzipFile('', 'rb', 9, StringIO(data))
            except zlib.error, msg:
                self.add_warning(_("Decompress error %(err)s") %
                                 {"err": str(msg)},
                                 tag=WARN_HTTP_DECOMPRESS_ERROR)
                f = StringIO(data)
            try:
                data = f.read()
            finally:
                f.close()
        # store temporary data
        self._data = data

    def encoding_supported (self):
        """Check if page encoding is supported."""
        encoding = headers.get_content_encoding(self.headers)
        if encoding and encoding not in _supported_encodings and \
           encoding != 'identity':
            self.add_warning(_("Unsupported content encoding `%(encoding)s'.") %
                             {"encoding": encoding},
                             tag=WARN_HTTP_UNSUPPORTED_ENCODING)
            return False
        return True

    def set_title_from_content (self):
        """Check if it's allowed to read content before execution."""
        if self.method_get_allowed:
            super(HttpUrl, self).set_title_from_content()

    def get_anchors (self):
        """Check if it's allowed to read content before execution."""
        if self.method_get_allowed:
            super(HttpUrl, self).get_anchors()

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
        if not (self.valid and self.headers):
            return False
        mime = self.get_content_type()
        if self.ContentMimetypes.get(mime) != "html":
            return False
        return self.encoding_supported()

    def is_css (self):
        """Return True iff content of this url is CSS stylesheet."""
        if not (self.valid and self.headers):
            return False
        mime = self.get_content_type()
        if self.ContentMimetypes.get(mime) != "css":
            return False
        return self.encoding_supported()

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
        if self.get_content_type() not in self.ContentMimetypes:
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
        if self.persistent and self.url_connection.is_idle():
            key = self.get_urlconnection_key()
            self.aggregate.connections.add(
                  key, self.url_connection, self.timeout)
        else:
            try:
                self.url_connection.close()
            except Exception:
                # ignore close errors
                pass
        self.url_connection = None

    def get_connection_key (self, scheme, host):
        """Get unique key specifying this connection.
        Used to reuse cached connections.
        @param scheme: 'https' or 'http'
        @ptype scheme: string
        @param host: host[:port]
        @ptype host: string
        @return: (scheme, host, port, user, password)
        @rtype: tuple(string, string, int, string, string)
        """
        host, port = urlutil.splitport(host)
        _user, _password = self.get_user_password()
        return (scheme, host, port, _user, _password)

    def get_urlconnection_key (self):
        """Get unique key specifying this connection.
        Used to cache connections.
        @return: (scheme, host, port, user, password)
        @rtype: tuple(string, string, int, string, string)
        """
        host, port = self.url_connection.host, self.url_connection.port
        if supportHttps and isinstance(self.url_connection, httplib.HTTPSConnection):
            scheme = 'https'
        else:
            scheme = 'http'
        _user, _password = self.get_user_password()
        return (scheme, host, port, _user, _password)
