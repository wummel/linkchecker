# -*- coding: iso-8859-1 -*-
"""Handle http links"""
# Copyright (C) 2000-2004  Bastian Kleineidam
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

import urlparse, sys, time, re, httplib2, zlib, gzip, robotparser2, socket
from urllib import quote, unquote
from cStringIO import StringIO
import Config, i18n
from linkcheck import LinkCheckerError
from debug import *
from ProxyUrlData import ProxyUrlData
from UrlData import ExcList, GetUrlDataFrom
supportHttps = hasattr(httplib2, "HTTPSConnection") and hasattr(socket, "ssl")

ExcList.extend([httplib2.error,])

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

# Amazon blocks HEAD requests at all
_isAmazonHost = re.compile(r'^www\.amazon\.(com|de|ca|fr|co\.(uk|jp))').search
# Servers not supporting HEAD request (eg returning 404 errors)
_isBrokenHeadServer = re.compile(r'(Netscape-Enterprise|Zope)/').search
# Server not supporting anchors in urls (eg returning 404 errors)
_isBrokenAnchorServer = re.compile(r'Microsoft-IIS/').search


class HttpUrlData (ProxyUrlData):
    "Url link with http scheme"

    def __init__ (self, urlName, recursionLevel, config, parentName=None,
                  baseRef=None, line=0, column=0, name=""):
        super(HttpUrlData, self).__init__(urlName, recursionLevel, config,
	                 parentName=parentName, baseRef=baseRef, line=line,
		         column=column, name=name)
        self.aliases = []
        self.max_redirects = 5
        self.has301status = False


    def buildUrl (self):
        super(HttpUrlData, self).buildUrl()
        # encode userinfo
        # XXX
        # check for empty paths
        if not self.urlparts[2]:
            self.setWarning(i18n._("URL path is empty, assuming '/' as path"))
            self.urlparts[2] = '/'
            self.url = urlparse.urlunsplit(self.urlparts)


    def checkConnection (self):
        """
        Check a URL with HTTP protocol.
        Here is an excerpt from RFC 1945 with common response codes:
        The first digit of the Status-Code defines the class of response. The
        last two digits do not have any categorization role. There are 5
        values for the first digit:
        o 1xx: Informational - Not used, but reserved for future use
        o 2xx: Success - The action was successfully received,
          understood, and accepted.
        o 3xx: Redirection - Further action must be taken in order to
          complete the request
        o 4xx: Client Error - The request contains bad syntax or cannot
          be fulfilled
        o 5xx: Server Error - The server failed to fulfill an apparently
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
        self.setProxy(self.config["proxy"].get(self.scheme))
        if self.proxy:
            self.setInfo(i18n._("Using Proxy %r")%self.proxy)
        self.headers = None
        self.auth = None
        self.cookies = []
        if not self.robotsTxtAllowsUrl():
            self.setWarning(i18n._("Access denied by robots.txt, checked only syntax"))
            return

        if _isAmazonHost(self.urlparts[1]):
            self.setWarning(i18n._("Amazon servers block HTTP HEAD requests, "
                                   "using GET instead"))
            self.method = "GET"
        else:
            # first try with HEAD
            self.method = "HEAD"
        fallback = False
        redirectCache = [self.url]
        while True:
            try:
                response = self._getHttpResponse()
            except httplib2.BadStatusLine:
                # some servers send empty HEAD replies
                if self.method=="HEAD":
                    self.method = "GET"
                    redirectCache = [self.url]
                    fallback = True
                    continue
                raise
            self.headers = response.msg
            debug(BRING_IT_ON, response.status, response.reason, self.headers)
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                self.setProxy(self.headers.getheader("Location"))
                self.setInfo(i18n._("Enforced Proxy %r")%self.proxy)
                response = self._getHttpResponse()
                self.headers = response.msg
                self.proxy, self.proxyauth = oldproxy
            # follow all redirections
            tries, response = self.followRedirections(response, redirectCache)
            if tries == -1:
                # already handled
                return
            if tries >= self.max_redirects:
                if self.method=="HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    self.method = "GET"
                    redirectCache = [self.url]
                    fallback = True
                    continue
                self.setError(i18n._("more than %d redirections, aborting")%self.max_redirects)
                return
            # user authentication
            if response.status == 401:
	        if not self.auth:
                    import base64
                    _user, _password = self.getUserPassword()
                    self.auth = "Basic "+\
                        base64.encodestring("%s:%s" % (_user, _password))
                    debug(BRING_IT_ON, "Authentication", _user, "/", _password)
                continue
            elif response.status >= 400:
                if self.headers:
                    # test for anchor support
                    server = self.headers.get('Server', '')
                    if _isBrokenAnchorServer(server) and self.urlparts[4]:
                        self.setWarning(i18n._("Server %r has no anchor support, removing anchor from request")%server)
                        self.urlparts[4] = ''
                        continue
                if self.method=="HEAD":
                    # fall back to GET
                    self.method = "GET"
                    redirectCache = [self.url]
                    fallback = True
                    continue
            elif self.headers and self.method!="GET":
                # test for HEAD support
                mime = self.headers.gettype()
                poweredby = self.headers.get('X-Powered-By', '')
                server = self.headers.get('Server', '')
                if mime=='application/octet-stream' and \
                   (poweredby.startswith('Zope') or \
                    server.startswith('Zope')):
                    self.setWarning(i18n._("Zope Server cannot determine"
                                " MIME type with HEAD, falling back to GET"))
                    continue
            break
        # check url warnings
        effectiveurl = urlparse.urlunsplit(self.urlparts)
        if self.url != effectiveurl:
            self.setWarning(i18n._("Effective URL %s") % effectiveurl)
            self.url = effectiveurl
        # check response
        self.checkResponse(response, fallback)


    def followRedirections (self, response, redirectCache):
        """follow all redirections of http response"""
        redirected = self.url
        tries = 0
        while response.status in [301,302] and self.headers and \
              tries < self.max_redirects:
            newurl = self.headers.getheader("Location",
                         self.headers.getheader("Uri", ""))
            redirected = unquote(urlparse.urljoin(redirected, newurl))
            # note: urlparts has to be a list
            self.urlparts = list(urlparse.urlsplit(redirected))
            # check internal redirect cache to avoid recursion
            if redirected in redirectCache:
                redirectCache.append(redirected)
                if self.method == "HEAD":
                    # Microsoft servers tend to recurse HEAD requests
                    # fall back to the original url and use GET
                    self.urlparts = list(urlparse.urlsplit(self.url))
                    return self.max_redirects, response
                self.setError(
                     i18n._("recursive redirection encountered:\n %s") % \
                            "\n  => ".join(redirectCache))
                return -1, response
            redirectCache.append(redirected)
            # remember this alias
            if response.status == 301:
                if not self.has301status:
                    self.setWarning(i18n._("HTTP 301 (moved permanent) encountered: you "
                                           "should update this link."))
                    if not (self.url.endswith('/') or self.url.endswith('.html')):
                        self.setWarning(i18n._("A HTTP 301 redirection occured and the url has no "
                                               "trailing / at the end. All urls which point to (home) "
                                               "directories should end with a / to avoid redirection."))
                    self.has301status = True
                self.aliases.append(redirected)
            # check cache again on possibly changed URL
            key = self.getCacheKey()
            if self.config.urlCache_has_key(key):
                self.copyFromCache(self.config.urlCache_get(key))
                self.cached = True
                self.logMe()
                return -1, response
            # check if we still have a http url, it could be another
            # scheme, eg https or news
            if self.urlparts[0]!="http":
                self.setWarning(i18n._("HTTP redirection to non-http url encountered; "
                                "the original url was %r.")%self.url)
                # make new UrlData object
                newobj = GetUrlDataFrom(redirected, self.recursionLevel, self.config,
                                        parentName=self.parentName, baseRef=self.baseRef,
                                        line=self.line, column=self.column, name=self.name)
                newobj.warningString = self.warningString
                newobj.infoString = self.infoString
                # append new object to queue
                self.config.appendUrl(newobj)
                # pretend to be finished and logged
                self.cached = True
                return -1, response
            # new response data
            response = self._getHttpResponse()
            self.headers = response.msg
            debug(BRING_IT_ON, "Redirected", self.headers)
            tries += 1
        return tries, response


    def checkResponse (self, response, fallback):
        """check final result"""
        if response.status >= 400:
            self.setError("%r %s"%(response.status, response.reason))
        else:
            if fallback:
                if self.headers and self.headers.has_key("Server"):
                    server = self.headers['Server']
                else:
                    server = i18n._("unknown")
                self.setWarning(i18n._("Server %r did not support HEAD request, used GET for checking")%server)
            if response.status == 204:
                # no content
                self.setWarning(response.reason)
            # store cookies for valid links
            if self.config['cookies']:
                for c in self.cookies:
                    self.setInfo("Cookie: %s"%c)
                out = self.config.storeCookies(self.headers, self.urlparts[1])
                for h in out:
                    self.setInfo(h)
            if response.status >= 200:
                self.setValid("%r %s"%(response.status,response.reason))
            else:
                self.setValid("OK")
        modified = self.headers.get('Last-Modified', '')
        if modified:
            self.setInfo(i18n._("Last modified %s") % modified)


    def getCacheKeys (self):
        keys = super(HttpUrlData, self).getCacheKeys()
        keys.extend(self.aliases)
        return keys


    def _getHttpResponse (self):
        """Put request and return (status code, status text, mime object).
           host can be host:port format
	"""
        if self.proxy:
            host = self.proxy
            scheme = "http"
        else:
            host = self.urlparts[1]
            scheme = self.urlparts[0]
        debug(HURT_ME_PLENTY, "host", host)
        if self.urlConnection:
            self.closeConnection()
        self.urlConnection = self.getHTTPObject(host, scheme)
        # quote parts before submit
        qurlparts = self.urlparts[:]
        qurlparts[2:5] = map(quote, self.urlparts[2:5])
        if self.proxy:
            path = urlparse.urlunsplit(qurlparts)
        else:
            path = urlparse.urlunsplit(('', '', qurlparts[2],
            qurlparts[3], qurlparts[4]))
        self.urlConnection.putrequest(self.method, path, skip_host=True)
        self.urlConnection.putheader("Host", host)
        # userinfo is from http://user@pass:host/
        if self.userinfo:
            self.urlConnection.putheader("Authorization", self.userinfo)
        # auth is the -u and -p configuration options
        elif self.auth:
            self.urlConnection.putheader("Authorization", self.auth)
        if self.proxyauth:
            self.urlConnection.putheader("Proxy-Authorization",
	                                 self.proxyauth)
        if self.parentName:
            self.urlConnection.putheader("Referer", self.parentName)
        self.urlConnection.putheader("User-Agent", Config.UserAgent)
        self.urlConnection.putheader("Accept-Encoding", "gzip;q=1.0, deflate;q=0.9, identity;q=0.5")
        if self.config['cookies']:
            self.cookies = self.config.getCookies(self.urlparts[1],
                                                  self.urlparts[2])
            for c in self.cookies:
                self.urlConnection.putheader("Cookie", c)
        self.urlConnection.endheaders()
        return self.urlConnection.getresponse()


    def getHTTPObject (self, host, scheme):
        if scheme=="http":
            h = httplib2.HTTPConnection(host)
        elif scheme=="https":
            h = httplib2.HTTPSConnection(host)
        else:
            raise LinkCheckerError, "invalid url scheme %s" % scheme
        h.set_debuglevel(get_debuglevel())
        h.connect()
        return h


    def getContent (self):
        if not self.has_content:
            self.method = "GET"
            self.has_content = True
            self.closeConnection()
            t = time.time()
            response = self._getHttpResponse()
            self.headers = response.msg
            self.data = response.read()
            encoding = self.headers.get("Content-Encoding")
            if encoding in _supported_encodings:
                try:
                    if encoding == 'deflate':
                        f = StringIO(zlib.decompress(self.data))
                    else:
                        f = gzip.GzipFile('', 'rb', 9, StringIO(self.data))
                except zlib.error:
                    f = StringIO(self.data)
                self.data = f.read()
            self.downloadtime = time.time() - t
        return self.data


    def isHtml (self):
        if not (self.valid and self.headers):
            return False
        if self.headers.gettype()[:9]!="text/html":
            return False
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding!='identity':
            self.setWarning(i18n._('Unsupported content encoding %r.')%encoding)
            return False
        return True


    def isHttp (self):
        return True


    def getContentType (self):
        ptype = self.headers.get('Content-Type', 'application/octet-stream')
        if ";" in ptype:
            ptype = ptype.split(';')[0]
        return ptype


    def isParseable (self):
        if not (self.valid and self.headers):
            return False
        if self.getContentType() not in ("text/html", "text/css"):
            return False
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding!='identity':
            self.setWarning(i18n._('Unsupported content encoding %r.')%encoding)
            return False
        return True


    def parseUrl (self):
        ptype = self.getContentType()
        if ptype=="text/html":
            self.parse_html()
        elif ptype=="text/css":
            self.parse_css()
        return None


    def getRobotsTxtUrl (self):
        return "%s://%s/robots.txt"%tuple(self.urlparts[0:2])


    def robotsTxtAllowsUrl (self):
        roboturl = self.getRobotsTxtUrl()
        debug(HURT_ME_PLENTY, "robots.txt url", roboturl)
        debug(HURT_ME_PLENTY, "url", self.url)
        if not self.config.robotsTxtCache_has_key(roboturl):
            rp = robotparser2.RobotFileParser()
            rp.set_url(roboturl)
            rp.read()
            self.config.robotsTxtCache_set(roboturl, rp)
        rp = self.config.robotsTxtCache_get(roboturl)
        return rp.can_fetch(Config.UserAgent, self.url)
