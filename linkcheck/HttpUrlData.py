# -*- coding: iso-8859-1 -*-
"""Handle http links"""
# Copyright (C) 2000-2003  Bastian Kleineidam
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

import urlparse, sys, time, re, httplib, robotparser2
from urllib import quote, unquote
import Config, i18n
from debug import *
# XXX not dynamic
if get_debuglevel() > 0:
    robotparser2.debug = 1
from ProxyUrlData import ProxyUrlData
from UrlData import ExcList, GetUrlDataFrom
supportHttps = hasattr(httplib, "HTTPSConnection")

ExcList.extend([httplib.error,])

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

# Amazon blocks HEAD requests at all
_isAmazonHost = re.compile(r'^www\.amazon\.(com|de|ca|fr|co\.(uk|jp))').search
# Servers not supporting HEAD request (eg returning 404 errors)
_isBrokenHeadServer = re.compile(r'Netscape-Enterprise/').search
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
            self.setInfo(i18n._("Using Proxy %s")%`self.proxy`)
        self.headers = None
        self.auth = None
        self.cookies = []
        if not self.robotsTxtAllowsUrl():
            self.setWarning(i18n._("Access denied by robots.txt, checked only syntax"))
            return

        # amazon servers suck
        if _isAmazonHost(self.urlparts[1]):
            self.setWarning(i18n._("Amazon servers block HTTP HEAD requests, "
                                   "using GET instead"))
        # first try
        redirectCache = [self.url]
        response = self._getHttpResponse()
        self.headers = response.msg
        debug(BRING_IT_ON, response.status, response.reason, self.headers)
        has301status = False
        while 1:
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                self.setProxy(self.headers.getheader("Location"))
                self.setInfo(i18n._("Enforced Proxy %s")%`self.proxy`)
                response = self._getHttpResponse()
                self.headers = response.msg
                self.proxy, self.proxyauth = oldproxy
            # follow redirections
            tries = 0
            redirected = self.url
            while response.status in [301,302] and self.headers and tries < 5:
                newurl = self.headers.getheader("Location",
                             self.headers.getheader("Uri", ""))
                redirected = unquote(urlparse.urljoin(redirected, newurl))
                # note: urlparts has to be a list
                self.urlparts = list(urlparse.urlsplit(redirected))
                # check internal redirect cache to avoid recursion
                if redirected in redirectCache:
                    redirectCache.append(redirected)
                    self.setError(
                         i18n._("recursive redirection encountered:\n %s") % \
                                "\n  => ".join(redirectCache))
                    return
                redirectCache.append(redirected)
                # remember this alias
                if response.status == 301:
                    if not has301status:
                        self.setWarning(i18n._("HTTP 301 (moved permanent) encountered: you "
                                               "should update this link."))
                        if not (self.url.endswith('/') or self.url.endswith('.html')):
                            self.setWarning(i18n._("A HTTP 301 redirection occured and the url has no "
                                                   "trailing / at the end. All urls which point to (home) "
                                                   "directories should end with a / to avoid redirection."))
                        has301status = True
                    self.aliases.append(redirected)
                # check cache again on possibly changed URL
                key = self.getCacheKey()
                if self.config.urlCache_has_key(key):
                    self.copyFrom(self.config.urlCache_get(key))
                    self.cached = True
                    self.logMe()
                    return
                # check if we still have a http url, it could be another
                # scheme, eg https or news
                if self.urlparts[0]!="http":
                    self.setWarning(i18n._("HTTP redirection to non-http url encountered; "
                                    "the original url was %s.") % `self.url`)
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
                    return
                # new response data
                response = self._getHttpResponse()
                self.headers = response.msg
                debug(BRING_IT_ON, "Redirected", self.headers)
                tries += 1
            if tries >= 5:
                self.setError(i18n._("more than five redirections, aborting"))
                return
            # user authentication
            if response.status==401:
	        if not self.auth:
                    import base64
                    _user, _password = self.getUserPassword()
                    self.auth = "Basic "+\
                        base64.encodestring("%s:%s" % (_user, _password))
                response = self._getHttpResponse()
                self.headers = response.msg
                debug(BRING_IT_ON, "Authentication", _user, "/", _password)
            # some servers get the HEAD request wrong:
            # - Netscape Enterprise Server (no HEAD implemented, 404 error)
            # - Hyperwave Information Server (501 error)
            # - Apache/1.3.14 (Unix) (500 error, http://www.rhino3d.de/)
            # - some advertisings (they want only GET, dont ask why ;)
            # - Zope server (it has to render the page to get the correct
            #   content-type)
            elif response.status in [405,501,500]:
                # HEAD method not allowed ==> try get
                self.setWarning(i18n._("Server does not support HEAD "
             "request (got %d status), falling back to GET")%response.status)
                response = self._getHttpResponse("GET")
                self.headers = response.msg
            elif response.status>=400 and self.headers:
                server = self.headers.get('Server', '')
                if _isBrokenHeadServer(server):
                    self.setWarning(i18n._("Server %s has no HEAD support, falling back to GET") % `server`)
                    response = self._getHttpResponse("GET")
                    self.headers = response.msg
                elif _isBrokenAnchorServer(server):
                    self.setWarning(i18n._("Server %s has no anchor support, removing anchor from request") % `server`)
                    self.urlparts[4] = ''
                    response = self._getHttpResponse()
                    self.headers = response.msg
            elif self.headers:
                type = self.headers.gettype()
                poweredby = self.headers.get('X-Powered-By', '')
                server = self.headers.get('Server', '')
                if type=='application/octet-stream' and \
                   (poweredby.startswith('Zope') or \
                    server.startswith('Zope')):
                    self.setWarning(i18n._("Zope Server cannot determine"
                                " MIME type with HEAD, falling back to GET"))
                    response = self._getHttpResponse("GET")
                    self.headers = response.msg
            if response.status not in [301,302]: break

        # check url warnings
        effectiveurl = urlparse.urlunsplit(self.urlparts)
        if self.url != effectiveurl:
            self.setWarning(i18n._("Effective URL %s") % effectiveurl)
            self.url = effectiveurl
        # check response
        self.checkResponse(response)


    def checkResponse (self, response):
        """check final result"""
        if response.status >= 400:
            self.setError(`response.status`+" "+response.reason)
        else:
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
                self.setValid(`response.status`+" "+response.reason)
            else:
                self.setValid("OK")


    def getCacheKeys (self):
        keys = super(HttpUrlData, self).getCacheKeys()
        keys.extend(self.aliases)
        return keys


    def _getHttpResponse (self, method="HEAD"):
        """Put request and return (status code, status text, mime object).
           host can be host:port format
	"""
        if _isAmazonHost(self.urlparts[1]):
            method = "GET"
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
        self.urlConnection.putrequest(method, path, skip_host=True)
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
            h = httplib.HTTPConnection(host)
        elif scheme=="https":
            h = httplib.HTTPSConnection(host)
        else:
            raise LinkCheckerError, "invalid url scheme %s" % scheme
        h.set_debuglevel(get_debuglevel())
        h.connect()
        return h


    def getContent (self):
        if not self.has_content:
            self.has_content = True
            self.closeConnection()
            t = time.time()
            response = self._getHttpResponse("GET")
            self.headers = response.msg
            self.data = response.read()
            encoding = self.headers.get("Content-Encoding")
            if encoding in _supported_encodings:
                from cStringIO import StringIO
                if encoding == 'deflate':
                    import zlib
                    f = StringIO(zlib.decompress(self.data))
                else:
                    import gzip
                    f = gzip.GzipFile('', 'rb', 9, StringIO(self.data))
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
            self.setWarning(i18n._('Unsupported content encoding %s.')%\
                            `encoding`)
            return False
        return True


    def isParseable (self):
        if not (self.valid and self.headers):
            return False
        if self.headers.gettype()[:9] not in ("text/html", "test/stylesheet"):
            return False
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding!='identity':
            self.setWarning(i18n._('Unsupported content encoding %s.')%\
                            `encoding`)
            return False
        return True


    def getRobotsTxtUrl (self):
        return self.urlparts[0]+"://"+self.urlparts[1]+"/robots.txt"


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
