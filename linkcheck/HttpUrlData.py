"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
import http11lib,urlparse,sys,time,re
from UrlData import UrlData
from RobotsTxt import RobotsTxt
import Config,StringUtil
from linkcheck import _

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
        | "400"   ; Bad Request
        | "401"   ; Unauthorized
        | "403"   ; Forbidden
        | "404"   ; Not Found
        | "405"   ; Method not allowed
        | "500"   ; Internal Server Error
        | "501"   ; Not Implemented
        | "502"   ; Bad Gateway
        | "503"   ; Service Unavailable
        | extension-code
        """
        
        self.mime = None
        self.auth = None
        self.proxy = config["proxy"]
        self.proxyport = config["proxyport"]
        if not self.urlTuple[2]:
            self.setWarning(_("Missing '/' at end of URL"))
        if config["robotstxt"] and not self.robotsTxtAllowsUrl(config):
            self.setWarning(_("Access denied by robots.txt, checked only syntax"))
            return
            
        # first try
        status, statusText, self.mime = self._getHttpRequest()
        Config.debug(str(status)+", "+str(statusText)+", "+str(self.mime)+"\n")
        has301status = 0
        while 1:
            # follow redirections
            tries = 0
            redirected = self.urlName
            while status in [301,302] and self.mime and tries < 5:
                has301status = (status==301)
                redirected = urlparse.urljoin(redirected, self.mime.getheader("Location"))
                self.urlTuple = urlparse.urlparse(redirected)
                status, statusText, self.mime = self._getHttpRequest()
                Config.debug("DEBUG: Redirected\n"+str(self.mime))
                tries = tries + 1

            # authentication
            if status==401:
	        if not self.auth:
                    import base64,string
                    _user, _password = self._getUserPassword(config)
                    self.auth = "Basic "+\
                        base64.encodestring("%s:%s" % (_user, _password))
                status, statusText, self.mime = self._getHttpRequest()
                Config.debug("DEBUG: Authentication "+_user+"/"+_password+"\n")

            # some servers get the HEAD request wrong:
            # - Netscape Enterprise Server III (no HEAD implemented, 404 error)
            # - Hyperwave Information Server (501 error)
            # - some advertisings (they want only GET, dont ask why ;)
            # - Zope server (it has to render the page to get the correct
            #   content-type
            elif status in [405,501]:
                # HEAD method not allowed ==> try get
                status, statusText, self.mime = self._getHttpRequest("GET")
                Config.debug("DEBUG: HEAD not supported\n")
            elif status>=400 and self.mime:
                server = self.mime.getheader("Server")
                if server and self.netscape_re.search(server):
                    status, statusText, self.mime = self._getHttpRequest("GET")
                    Config.debug("DEBUG: Netscape Enterprise Server detected\n")
            elif self.mime:
                type = self.mime.gettype()
                poweredby = self.mime.getheader('X-Powered-By')
                server = self.mime.getheader('Server')
                if type=='application/octet-stream' and \
                   ((poweredby and poweredby[:4]=='Zope') or \
                    (server and server[:4]=='Zope')):
                    status,statusText,self.mime = self._getHttpRequest("GET")

            if status not in [301,302]: break

        effectiveurl = urlparse.urlunparse(self.urlTuple)
        if self.url != effectiveurl:
            self.setWarning(_("Effective URL %s") % effectiveurl)
            self.url = effectiveurl

        if has301status:
            self.setWarning(_("HTTP 301 (moved permanent) encountered: "
	                    "you should update this link"))
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

        
    def _getHttpRequest(self, method="HEAD"):
        "Put request and return (status code, status text, mime object)"
        if self.proxy:
            Config.debug("DEBUG: using proxy %s:%d\n" %
	                 (self.proxy,self.proxyport))
            host = '%s:%d' % (self.proxy, self.proxyport)
        else:
            host = self.urlTuple[1]
        if self.urlConnection:
            self.closeConnection()
        self.urlConnection = self._getHTTPObject(host)
        if self.proxy:
            path = urlparse.urlunparse(self.urlTuple)
        else:
            path = self.urlTuple[2]
            if self.urlTuple[3]:
                path = path + ";" + self.urlTuple[3]
            if self.urlTuple[4]:
                path = path + "?" + self.urlTuple[4]
        self.urlConnection.putrequest(method, path)
        self.urlConnection.putheader("Host", self.urlTuple[1])
        if self.auth:
            self.urlConnection.putheader("Authorization", self.auth)
        self.urlConnection.putheader("User-agent", Config.UserAgent)
        self.urlConnection.endheaders()
        return self.urlConnection.getreply()

    def _getHTTPObject(self, host):
        return http11lib.HTTP(host)

    def getContent(self):
        if not self.data:
            self.closeConnection()
            t = time.time()
            status, statusText, self.mime = self._getHttpRequest("GET")
            self.urlConnection = self.urlConnection.getfile()
            self.data = self.urlConnection.read()
            self.downloadtime = time.time() - t
            self._init_html_comments()
            Config.debug("DEBUG: comment spans %s\n" % self.html_comments)
        return self.data
        
    def isHtml(self):
        if not (self.valid and self.mime):
            return 0
        return self.mime.gettype()=="text/html"

    def robotsTxtAllowsUrl(self, config):
        try:
            if config.robotsTxtCache_has_key(self.urlTuple[1]):
                robotsTxt = config.robotsTxtCache_get(self.urlTuple[1])
            else:
                robotsTxt = RobotsTxt(self.urlTuple, Config.UserAgent)
                Config.debug("DEBUG: "+str(robotsTxt)+"\n")
                config.robotsTxtCache_set(self.urlTuple[1], robotsTxt)
        except:
            type, value = sys.exc_info()[:2]
            Config.debug("Heieiei: "+str(value)+"\n")
            return 1
        return robotsTxt.allowance(Config.UserAgent, self.urlTuple[2])


    def __str__(self):
        return "HTTP link\n"+UrlData.__str__(self)

    def closeConnection(self):
        if self.mime:
            try: self.mime.close()
            except: pass
            self.mime = None
        UrlData.closeConnection(self)
