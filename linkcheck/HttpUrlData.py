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

import httplib, urlparse, sys, time, re
import Config, StringUtil, robotparser
from UrlData import UrlData
from urllib import splittype, splithost, splituser, splitpasswd
from linkcheck import _
from debuglevels import *

class HttpUrlData(UrlData):
    "Url link with http scheme"
    netscape_re = re.compile("Netscape-Enterprise/")

    def checkConnection(self, config):
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

        self._setProxy(config["proxy"].get(self.scheme))
        self.mime = None
        self.auth = None
        self.proxyauth = None
        if not self.urlTuple[2]:
            self.setWarning(_("Missing '/' at end of URL"))
        if config["robotstxt"] and not self.robotsTxtAllowsUrl(config):
            self.setWarning(_("Access denied by robots.txt, checked only syntax"))
            return

        # first try
        status, statusText, self.mime = self._getHttpRequest()
        Config.debug(BRING_IT_ON, status, statusText, self.mime)
        has301status = 0
        while 1:

            # proxy enforcement (overrides standard proxy)
            if status == 305 and self.mime:
                self._setProxy(self.mime.get("Location"))
                status, statusText, self.mime = self._getHttpRequest()

            # proxy authentication
            if status==407:
                if not (self.proxyuser and self.proxypass):
                    break
                if not self.proxyauth:
                    import base64
                    self.proxyauth = "Basic "+base64.encodestring("%s:%s" % \
			(self.proxyuser, self.proxypass))
                    status, statusText, self.mime = self._getHttpRequest()

            # follow redirections
            tries = 0
            redirected = self.urlName
            while status in [301,302] and self.mime and tries < 5:
                has301status = (status==301)
                newurl = self.mime.get("Location", self.mime.get("Uri", ""))
                redirected = urlparse.urljoin(redirected, newurl)
                self.urlTuple = urlparse.urlparse(redirected)
                status, statusText, self.mime = self._getHttpRequest()
                Config.debug(BRING_IT_ON, "Redirected", self.mime)
                tries += 1
            if tries >= 5:
                self.setError(_("too much redirections (>= 5)"))
                return

            # user authentication
            if status==401:
	        if not self.auth:
                    import base64
                    _user, _password = self._getUserPassword(config)
                    self.auth = "Basic "+\
                        base64.encodestring("%s:%s" % (_user, _password))
                status, statusText, self.mime = self._getHttpRequest()
                Config.debug(BRING_IT_ON, "Authentication", _user, "/",
		             _password)

            # some servers get the HEAD request wrong:
            # - Netscape Enterprise Server III (no HEAD implemented, 404 error)
            # - Hyperwave Information Server (501 error)
            # - Apache/1.3.14 (Unix) (500 error, http://www.rhino3d.de/)
            # - some advertisings (they want only GET, dont ask why ;)
            # - Zope server (it has to render the page to get the correct
            #   content-type
            elif status in [405,501,500]:
                # HEAD method not allowed ==> try get
                self.setWarning(_("Server does not support HEAD request (got %d status), falling back to GET")%status)
                status, statusText, self.mime = self._getHttpRequest("GET")
            elif status>=400 and self.mime:
                server = self.mime.getheader("Server")
                if server and self.netscape_re.search(server):
                    self.setWarning(_("Netscape Enterprise Server with no HEAD support, falling back to GET"))
                    status, statusText, self.mime = self._getHttpRequest("GET")
            elif self.mime:
                type = self.mime.gettype()
                poweredby = self.mime.getheader('X-Powered-By')
                server = self.mime.getheader('Server')
                if type=='application/octet-stream' and \
                   ((poweredby and poweredby[:4]=='Zope') or \
                    (server and server[:4]=='Zope')):
                    self.setWarning(_("Zope Server cannot determine MIME type with HEAD, falling back to GET"))
                    status,statusText,self.mime = self._getHttpRequest("GET")

            if status not in [301,302]: break

        effectiveurl = urlparse.urlunparse(self.urlTuple)
        if self.url != effectiveurl:
            self.setWarning(_("Effective URL %s") % effectiveurl)
            self.url = effectiveurl

        if has301status:
            self.setWarning(_("HTTP 301 (moved permanent) encountered: you "
                              "should update this link"))
            if self.url[-1]!='/':
                self.setWarning(_("A HTTP 301 redirection occured and the url has no "
                     "trailing / at the end. All urls which point to (home) "
                     "directories should end with a / to avoid redirection"))

        # check final result
        if status >= 400:
            self.setError(`status`+" "+statusText)
        else:
            if status == 204:
                # no content
                self.setWarning(statusText)
            if status >= 200:
                self.setValid(`status`+" "+statusText)
            else:
                self.setValid("OK")


    def _setProxy(self, proxy):
        self.proxy = proxy
        self.proxyuser = None
        self.proxypass = None
        if self.proxy:
            self.proxy = splittype(self.proxy)[1]
            self.proxy = splithost(self.proxy)[0]
            self.proxyuser, self.proxy = splituser(self.proxy)
            if self.proxyuser:
                self.proxyuser, self.proxypass = splitpasswd(self.proxyuser)


    def _getHttpRequest(self, method="HEAD"):
        """Put request and return (status code, status text, mime object).
           host can be host:port format
	"""
        if self.proxy:
            host = self.proxy
        else:
            host = self.urlTuple[1]

        if self.urlConnection:
            self.closeConnection()
        self.urlConnection = self._getHTTPObject(host)
        if self.proxy:
            path = urlparse.urlunparse(self.urlTuple)
        else:
            path = urlparse.urlunparse(('', '', self.urlTuple[2],
            self.urlTuple[3], self.urlTuple[4], ''))
        self.urlConnection.putrequest(method, path)
        self.urlConnection.putheader("Host", host)
        if self.auth:
            self.urlConnection.putheader("Authorization", self.auth)
        if self.proxyauth:
            self.urlConnection.putheader("Proxy-Authorization",
	        self.proxyauth)
        self.urlConnection.putheader("User-agent", Config.UserAgent)
        self.urlConnection.endheaders()
        return self.urlConnection.getreply()

    def _getHTTPObject(self, host):
        h = httplib.HTTP()
        h.set_debuglevel(Config.DebugLevel)
        h.connect(host)
        return h

    def getContent(self):
        if not self.has_content:
            self.has_content = 1
            self.closeConnection()
            t = time.time()
            status, statusText, self.mime = self._getHttpRequest("GET")
            self.urlConnection = self.urlConnection.getfile()
            self.data = self.urlConnection.read()
            self.downloadtime = time.time() - t
            self.init_html_comments()
            Config.debug(HURT_ME_PLENTY, "comment spans", self.html_comments)
        return self.data

        
    def isHtml(self):
        if not (self.valid and self.mime):
            return 0
        return self.mime.gettype()[:9]=="text/html"


    def robotsTxtAllowsUrl(self, config):
        roboturl="%s://%s/robots.txt" % self.urlTuple[0:2]
        if not config.robotsTxtCache_has_key(roboturl):
            rp = robotparser.RobotFileParser(roboturl)
            rp.read()
            config.robotsTxtCache_set(roboturl, rp)
        rp = config.robotsTxtCache_get(roboturl)
        return rp.can_fetch(Config.UserAgent, self.url)


    def closeConnection(self):
        if self.mime:
            try: self.mime.close()
            except: pass
            self.mime = None
        UrlData.closeConnection(self)
