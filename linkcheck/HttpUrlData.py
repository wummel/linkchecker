"""Handle http links"""
# Copyright (C) 2000,2001  Bastian Kleineidam
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

import urlparse, urllib, sys, time, re
import httplib
import Config, StringUtil, robotparser, linkcheck
# XXX not dynamic
if Config.DebugLevel > 0:
    robotparser.debug = 1
from ProxyUrlData import ProxyUrlData
from debuglevels import *

_supported_encodings = ('gzip', 'x-gzip', 'deflate')

class HttpUrlData (ProxyUrlData):
    "Url link with http scheme"
    netscape_re = re.compile("Netscape-Enterprise/")

    def buildUrl (self):
        ProxyUrlData.buildUrl(self)
        # encode userinfo
        # XXX
        # check for empty paths
        if not self.urlparts[2]:
            self.setWarning(linkcheck._("Path is empty"))
            self.urlparts[2] = "/"
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
            self.setInfo(linkcheck._("Using Proxy %s")%`self.proxy`)
        self.headers = None
        self.auth = None
        self.cookies = []
        if self.config["robotstxt"] and not self.robotsTxtAllowsUrl():
            self.setWarning(linkcheck._("Access denied by robots.txt, checked only syntax"))
            return

        # first try
        response = self._getHttpResponse()
        self.headers = response.msg
        Config.debug(BRING_IT_ON, response.status, response.reason, self.headers)
        has301status = 0
        while 1:
            # proxy enforcement (overrides standard proxy)
            if response.status == 305 and self.headers:
                oldproxy = (self.proxy, self.proxyauth)
                self.setProxy(self.headers.getheader("Location"))
                self.setInfo(linkcheck._("Enforced Proxy %s")%`self.proxy`)
                response = self._getHttpResponse()
                self.headers = response.msg
                self.proxy, self.proxyauth = oldproxy
            # follow redirections
            tries = 0
            redirected = self.urlName
            while response.status in [301,302] and self.headers and tries < 5:
                has301status = (response.status==301)
                newurl = self.headers.getheader("Location",
                             self.headers.getheader("Uri", ""))
                redirected = urlparse.urljoin(redirected, newurl)
                redirected = urllib.unquote(redirected)
                self.urlparts = urlparse.urlsplit(redirected)
                response = self._getHttpResponse()
                self.headers = response.msg
                Config.debug(BRING_IT_ON, "Redirected", self.headers)
                tries += 1
            if tries >= 5:
                self.setError(linkcheck._("too much redirections (>= 5)"))
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
                Config.debug(BRING_IT_ON, "Authentication", _user, "/",
		             _password)
            # some servers get the HEAD request wrong:
            # - Netscape Enterprise Server (no HEAD implemented, 404 error)
            # - Hyperwave Information Server (501 error)
            # - Apache/1.3.14 (Unix) (500 error, http://www.rhino3d.de/)
            # - some advertisings (they want only GET, dont ask why ;)
            # - Zope server (it has to render the page to get the correct
            #   content-type)
            elif response.status in [405,501,500]:
                # HEAD method not allowed ==> try get
                self.setWarning(linkcheck._("Server does not support HEAD "
             "request (got %d status), falling back to GET")%response.status)
                response = self._getHttpResponse("GET")
                self.headers = response.msg
            elif response.status>=400 and self.headers:
                server = self.headers.getheader("Server")
                if server and self.netscape_re.search(server):
                    self.setWarning(linkcheck._("Netscape Enterprise Server"
                     " with no HEAD support, falling back to GET"))
                    response = self._getHttpResponse("GET")
                    self.headers = response.msg
            elif self.headers:
                type = self.headers.gettype()
                poweredby = self.headers.getheader('X-Powered-By')
                server = self.headers.getheader('Server')
                if type=='application/octet-stream' and \
                   ((poweredby and poweredby[:4]=='Zope') or \
                    (server and server[:4]=='Zope')):
                    self.setWarning(linkcheck._("Zope Server cannot determine"
                                " MIME type with HEAD, falling back to GET"))
                    response = self._getHttpResponse("GET")
                    self.headers = response.msg
            if response.status not in [301,302]: break

        effectiveurl = urlparse.urlunsplit(self.urlparts)
        if self.url != effectiveurl:
            self.setWarning(linkcheck._("Effective URL %s") % effectiveurl)
            self.url = effectiveurl

        if has301status:
            self.setWarning(linkcheck._("HTTP 301 (moved permanent) encountered: you "
                              "should update this link"))
            if self.url[-1]!='/':
                self.setWarning(
            linkcheck._("A HTTP 301 redirection occured and the url has no "
                    "trailing / at the end. All urls which point to (home) "
                    "directories should end with a / to avoid redirection"))

        # check final result
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

    def _getHttpResponse (self, method="HEAD"):
        """Put request and return (status code, status text, mime object).
           host can be host:port format
	"""
        if self.proxy:
            host = self.proxy
        else:
            host = self.urlparts[1]
        Config.debug(HURT_ME_PLENTY, "host", host)
        if self.urlConnection:
            self.closeConnection()
        self.urlConnection = self._getHTTPObject(host)
        if self.proxy:
            path = urlparse.urlunsplit(self.urlparts)
        else:
            path = urlparse.urlunsplit(('', '', self.urlparts[2],
            self.urlparts[3], self.urlparts[4]))
        self.urlConnection.putrequest(method, path, skip_host=1)
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

    def _getHTTPObject (self, host):
        h = httplib.HTTPConnection(host)
        h.set_debuglevel(Config.DebugLevel)
        h.connect()
        return h

    def getContent (self):
        if not self.has_content:
            self.has_content = 1
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
            return 0
        if self.headers.gettype()[:9]!="text/html":
            return 0
        encoding = self.headers.get("Content-Encoding")
        if encoding and encoding not in _supported_encodings and \
           encoding!='identity':
            self.setWarning(linkcheck._('Unsupported content encoding %s.')%\
                            `encoding`)
            return 0
        return 1

    def robotsTxtAllowsUrl (self):
        roboturl = self.urlparts[0]+"://"+self.urlparts[1]+"/robots.txt"
        Config.debug(HURT_ME_PLENTY, "robots.txt url", roboturl)
        Config.debug(HURT_ME_PLENTY, "url", self.url)
        if not self.config.robotsTxtCache_has_key(roboturl):
            rp = robotparser.RobotFileParser()
            rp.set_url(roboturl)
            rp.read()
            self.config.robotsTxtCache_set(roboturl, rp)
        rp = self.config.robotsTxtCache_get(roboturl)
        return rp.can_fetch(Config.UserAgent, self.url)
