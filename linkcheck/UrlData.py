# -*- coding: iso-8859-1 -*-
"""Base URL handler"""
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

import sys, re, urlparse, urllib2, time, traceback, socket, select, i18n
from urllib import splituser, splitport, unquote
from linkcheck import DNS, LinkCheckerError, getLinkPat
from linkcheck.parser import htmlsax
DNS.DiscoverNameServers()

import Config, StringUtil, test_support
from linkparse import LinkFinder, MetaRobotsFinder
from debug import *

ws_at_start_or_end = re.compile(r"(^\s+)|(\s+$)").search

# helper function for internal errors
def internal_error ():
    print >>sys.stderr, i18n._("""\n********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
1) The URL or file you are testing
2) Your commandline arguments and/or configuration.
3) The system information below.

If you disclose some information because its too private to you thats ok.
I will try to help you nontheless (but you have to give me *something*
I can work with ;).
""") % Config.Email
    type, value = sys.exc_info()[:2]
    print >>sys.stderr, type, value
    traceback.print_exc()
    print_app_info()
    print >>sys.stderr, i18n._("\n******** LinkChecker internal error, bailing out ********")
    sys.exit(1)


def print_app_info ():
    import os
    print >>sys.stderr, i18n._("System info:")
    print >>sys.stderr, Config.App
    print >>sys.stderr, "Python %s on %s" % (sys.version, sys.platform)
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >>sys.stderr, key, "=", repr(value)


def get_absolute_url (urlName, baseRef, parentName):
    """Search for the absolute url to detect the link type. This does not
       join any url fragments together! Returns the url in lower case to
       simplify urltype matching."""
    if urlName and ":" in urlName:
        return urlName.lower()
    elif baseRef and ":" in baseRef:
        return baseRef.lower()
    elif parentName and ":" in parentName:
        return parentName.lower()
    return ""


# we catch these exceptions, all other exceptions are internal
# or system errors
ExcList = [
   IOError,
   ValueError, # from httplib.py
   LinkCheckerError,
   DNS.Error,
   socket.timeout,
   socket.error,
   select.error,
]

if hasattr(socket, "sslerror"):
    ExcList.append(socket.sslerror)

# regular expression for port numbers
is_valid_port = re.compile(r"\d+").match


def GetUrlDataFrom (urlName, recursionLevel, config, parentName=None,
                    baseRef=None, line=0, column=0, name=None,
                    cmdline=None):
    from FileUrlData import FileUrlData
    from IgnoredUrlData import IgnoredUrlData, ignored_schemes_re
    from FtpUrlData import FtpUrlData
    from GopherUrlData import GopherUrlData
    from HttpUrlData import HttpUrlData
    from HttpsUrlData import HttpsUrlData
    from MailtoUrlData import MailtoUrlData
    from TelnetUrlData import TelnetUrlData
    from NntpUrlData import NntpUrlData
    url = get_absolute_url(urlName, baseRef, parentName)
    # test scheme
    if url.startswith("http:"):
        klass = HttpUrlData
    elif url.startswith("ftp:"):
        klass = FtpUrlData
    elif url.startswith("file:"):
        klass = FileUrlData
    elif url.startswith("telnet:"):
        klass = TelnetUrlData
    elif url.startswith("mailto:"):
        klass = MailtoUrlData
    elif url.startswith("gopher:"):
        klass = GopherUrlData
    elif url.startswith("https:"):
        klass = HttpsUrlData
    elif url.startswith("nttp:") or \
         url.startswith("news:") or \
         url.startswith("snews:"):
        klass = NntpUrlData
    # application specific links are ignored
    elif ignored_schemes_re.search(url):
        klass = IgnoredUrlData
    # assume local file
    else:
        klass = FileUrlData
    if config['strict'] and cmdline and \
       not (config['internlinks'] or config['externlinks']):
        # set automatic intern/extern stuff if no filter was given
        set_intern_url(url, klass, config)
    return klass(urlName, recursionLevel, config, parentName, baseRef,
                 line=line, column=column, name=name)


def set_intern_url (url, klass, config):
    """Precondition: config['strict'] is true (ie strict checking) and
       recursion level is zero (ie url given on the command line)"""
    from FileUrlData import FileUrlData
    from FtpUrlData import FtpUrlData
    from HttpUrlData import HttpUrlData
    from HttpsUrlData import HttpsUrlData
    if klass == FileUrlData:
        debug(BRING_IT_ON, "Add intern pattern ^file:")
        config['internlinks'].append(getLinkPat("^file:"))
    elif klass in [HttpUrlData, HttpsUrlData, FtpUrlData]:
        domain = urlparse.urlsplit(url)[1]
        if domain:
            domain = "://%s"%re.escape(domain)
            debug(BRING_IT_ON, "Add intern domain", domain)
            # add scheme colon to link pattern
            config['internlinks'].append(getLinkPat(domain))


class UrlData (object):
    "Representing a URL with additional information like validity etc"

    def __init__ (self,
                  urlName,
                  recursionLevel,
                  config,
                  parentName = None,
                  baseRef = None,
                  line = 0,
                  column = 0,
		  name = ""):
        self.urlName = urlName
        self.anchor = None
        self.recursionLevel = recursionLevel
        self.config = config
        self.parentName = parentName
        self.baseRef = baseRef
        self.errorString = i18n._("Error")
        self.validString = i18n._("Valid")
        self.warningString = None
        self.infoString = None
        self.valid = True
        self.url = None
	self.urlparts = None
        self.line = line
        self.column = column
        self.name = name
        self.dltime = -1
        self.dlsize = -1
        self.checktime = 0
        self.cached = False
        self.urlConnection = None
        self.extern = (1, 0)
        self.data = None
        self.has_content = False
        url = get_absolute_url(self.urlName, self.baseRef, self.parentName)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0] or "file"


    def setError (self, s):
        self.valid = False
        self.errorString = i18n._("Error")+": "+s


    def setValid (self, s):
        self.valid = True
        self.validString = i18n._("Valid")+": "+s


    def isParseable (self):
        return False


    def isHtml (self):
        return False


    def setWarning (self, s):
        if self.warningString:
            self.warningString += "\n"+s
        else:
            self.warningString = s


    def setInfo (self, s):
        if self.infoString:
            self.infoString += "\n"+s
        else:
            self.infoString = s


    def copyFromCache (self, cacheData):
        self.errorString = cacheData["errorString"]
        self.validString = cacheData["validString"]
        if self.warningString:
            if cacheData["warningString"]:
                self.warningString += "\n"+cacheData["warningString"]
        else:
            self.warningString = cacheData["warningString"]
        self.infoString = cacheData["infoString"]
        self.valid = cacheData["valid"]
        self.dltime = cacheData["dltime"]


    def getCacheData (self):
        return {"errorString": self.errorString,
                "validString": self.validString,
                "warningString": self.warningString,
                "infoString": self.infoString,
                "valid": self.valid,
                "dltime": self.dltime,
               }


    def buildUrl (self):
        if self.baseRef:
            if ":" not in self.baseRef:
                self.baseRef = urlparse.urljoin(self.parentName, self.baseRef)
            self.url = urlparse.urljoin(self.baseRef, self.urlName)
        elif self.parentName:
            self.url = urlparse.urljoin(self.parentName, self.urlName)
        else:
            self.url = self.urlName
        # unquote url
        self.url = unquote(self.url)
        # split into (modifiable) list
        self.urlparts = list(urlparse.urlsplit(self.url))
        # check userinfo@host:port syntax
        self.userinfo, host = splituser(self.urlparts[1])
        x, port = splitport(host)
        if port is not None and not is_valid_port(port):
            raise LinkCheckerError(i18n._("URL has invalid port number %r")\
                                  % str(port))
        # set host lowercase and without userinfo
        self.urlparts[1] = host.lower()
        # safe anchor for later checking
        self.anchor = self.urlparts[4]


    def logMe (self):
        debug(BRING_IT_ON, "logging url")
        self.config.incrementLinknumber()
        if self.config["verbose"] or not self.valid or \
           (self.warningString and self.config["warnings"]):
            self.config.log_newUrl(self)


    def check (self):
        try:
            self._check()
        except KeyboardInterrupt:
            raise
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            type, value = sys.exc_info()[:2]
            if type!=4:
                raise
        except test_support.Error:
            raise
        except:
            internal_error()


    def _check (self):
        debug(BRING_IT_ON, "Checking", self)
        if self.recursionLevel and self.config['wait']:
            debug(BRING_IT_ON, "sleeping for", self.config['wait'], "seconds")
            time.sleep(self.config['wait'])
        t = time.time()
        # check syntax
        debug(BRING_IT_ON, "checking syntax")
        if not self.urlName or self.urlName=="":
            self.setError(i18n._("URL is null or empty"))
            self.logMe()
            return
        if ws_at_start_or_end(self.urlName):
            self.setError(i18n._("URL has whitespace at beginning or end"))
            self.logMe()
            return
        try:
	    self.buildUrl()
            self.extern = self._getExtern()
        except tuple(ExcList):
            value, tb = sys.exc_info()[1:]
            debug(HURT_ME_PLENTY, "exception", traceback.format_tb(tb))
            self.setError(str(value))
            self.logMe()
            return

        # check the cache
        debug(BRING_IT_ON, "checking cache")
        for key in self.getCacheKeys():
            if self.config.urlCache_has_key(key):
                self.copyFromCache(self.config.urlCache_get(key))
                self.cached = True
                self.logMe()
                return

        # apply filter
        debug(BRING_IT_ON, "extern =", self.extern)
        if self.extern[0] and (self.config["strict"] or self.extern[1]):
            self.setWarning(
                  i18n._("outside of domain filter, checked only syntax"))
            self.logMe()
            return

        # check connection
        debug(BRING_IT_ON, "checking connection")
        try:
            self.checkConnection()
            if self.cached:
                return
            if self.config["anchors"]:
                self.checkAnchors()
        except tuple(ExcList):
            etype, evalue, etb = sys.exc_info()
            debug(HURT_ME_PLENTY, "exception", traceback.format_tb(etb))
            # make nicer error msg for unknown hosts
            if isinstance(evalue, socket.error) and evalue[0]==-2:
                evalue = i18n._('Hostname not found')
            self.setError(str(evalue))

        # check content
        warningregex = self.config["warningregex"]
        if warningregex and self.valid:
            debug(BRING_IT_ON, "checking content")
            try:
                self.checkContent(warningregex)
            except tuple(ExcList):
                value, tb = sys.exc_info()[1:]
                debug(HURT_ME_PLENTY, "exception", traceback.format_tb(tb))
                self.setError(str(value))

        self.checktime = time.time() - t
        # check recursion
        debug(BRING_IT_ON, "checking recursion")
        try:
            if self.allowsRecursion():
                self.parseUrl()
            # check content size
            self.checkSize()
        except tuple(ExcList):
            value, tb = sys.exc_info()[1:]
            debug(HURT_ME_PLENTY, "exception", traceback.format_tb(tb))
            self.setError(i18n._("could not parse content: %r")%str(value))
        # close
        self.closeConnection()
        self.logMe()
        debug(BRING_IT_ON, "caching")
        self.putInCache()


    def closeConnection (self):
        # brute force closing
        if self.urlConnection is not None:
            try: self.urlConnection.close()
            except: pass
            # release variable for garbage collection
            self.urlConnection = None


    def putInCache (self):
        if not self.cached:
            data = self.getCacheData()
            for key in self.getCacheKeys():
                self.config.urlCache_set(key, data)
                self.config.urlSeen_set(key)
            self.cached = True


    def getCacheKeys (self):
        key = self.getCacheKey()
        if key is None:
            return []
        return [key]


    def isCached (self):
        key = self.getCacheKey()
        return self.cached or self.config.urlSeen_has_key(key)


    def getCacheKey (self):
        # note: the host is already lowercase
        if self.urlparts:
            if self.config["anchorcaching"]:
                # do not ignore anchor
                return urlparse.urlunsplit(self.urlparts)
            else:
                # removed anchor from cache key
                return urlparse.urlunsplit(self.urlparts[:4]+[''])
        return None


    def checkConnection (self):
        self.urlConnection = urllib2.urlopen(self.url)


    def allowsRecursion (self):
        # note: test self.valid before self.isParseable()
        return self.valid and \
               self.isParseable() and \
               self.hasContent() and \
               self.contentAllowsRobots() and \
               not self.isCached() and \
               (self.config["recursionlevel"] < 0 or
                self.recursionLevel < self.config["recursionlevel"]) and \
               not self.extern[0]


    def contentAllowsRobots (self):
        if not self.isHtml():
            return True
        h = MetaRobotsFinder(self.getContent())
        p = htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        return h.follow


    def checkAnchors (self):
        if not (self.valid and self.anchor and self.isHtml() and \
                self.hasContent()):
            # do not bother
            return
        debug(HURT_ME_PLENTY, "checking anchor", self.anchor)
        h = LinkFinder(self.getContent(), tags={'a': ['name'], None: ['id']})
        p = htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        for cur_anchor,line,column,name,base in h.urls:
            if cur_anchor == self.anchor:
                return
        self.setWarning(i18n._("anchor #%s not found") % self.anchor)


    def _getExtern (self):
        if not (self.config["externlinks"] or self.config["internlinks"]):
            return (0, 0)
        # deny and allow external checking
        Config.debug(HURT_ME_PLENTY, "Url", self.url)
        if self.config["denyallow"]:
            for entry in self.config["externlinks"]:
                Config.debug(HURT_ME_PLENTY, "Extern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            for entry in self.config["internlinks"]:
                Config.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            return (0, 0)
        else:
            for entry in self.config["internlinks"]:
                Config.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            for entry in self.config["externlinks"]:
                Config.debug(HURT_ME_PLENTY, "Extern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            return (1,0)


    def hasContent (self):
        """indicate wether url getContent() can be called"""
        return True


    def getContent (self):
        """Precondition: urlConnection is an opened URL."""
        if not self.has_content:
            self.has_content = True
            t = time.time()
            self.data = self.urlConnection.read()
            self.dltime = time.time() - t
            self.dlsize = len(self.data)
        return self.data


    def checkContent (self, warningregex):
        """if a warning expression was given, call this function to check it
           against the content of this url"""
        if not self.hasContent():
            return
        match = warningregex.search(self.getContent())
        if match:
            self.setWarning(i18n._("Found %r in link contents")%match.group())


    def checkSize (self):
        """if a maximum size was given, call this function to check it
           against the content size of this url"""
        maxbytes = self.config["warnsizebytes"]
        if maxbytes is not None and self.dlsize >= maxbytes:
            self.setWarning(i18n._("Content size %s is larger than %s")%\
                         (StringUtil.strsize(self.dlsize),
                          StringUtil.strsize(maxbytes)))


    def parseUrl (self):
        # default parse type is html
        debug(BRING_IT_ON, "Parsing recursively into", self)
        self.parse_html();


    def getUserPassword (self):
        for auth in self.config["authentication"]:
            if auth['pattern'].match(self.url):
                return auth['user'], auth['password']
        return None,None


    def parse_html (self):
        # search for a possible base reference
        h = LinkFinder(self.getContent(), tags={'base': ['href']})
        p = htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        baseRef = None
        if len(h.urls)>=1:
            baseRef = h.urls[0][0]
            if len(h.urls)>1:
                self.setWarning(i18n._(
                "more than one <base> tag found, using only the first one"))
        h = LinkFinder(self.getContent())
        p = htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        for s in h.parse_info:
            # the parser had warnings/errors
            self.setWarning(s)
        for url,line,column,name,codebase in h.urls:
            if codebase:
                base = codebase
            else:
                base = baseRef
            self.config.appendUrl(GetUrlDataFrom(url,
                                  self.recursionLevel+1, self.config,
                                  parentName=self.url, baseRef=base,
                                  line=line, column=column, name=name))


    def parse_opera (self):
        # parse an opera bookmark file
        name = ""
        lineno = 0
        lines = self.getContent().splitlines()
        for line in lines:
            lineno += 1
            line = line.strip()
            if line.startswith("NAME="):
                name = line[5:]
            elif line.startswith("URL="):
                url = line[4:]
                if url:
                    self.config.appendUrl(GetUrlDataFrom(url,
           self.recursionLevel+1, self.config, self.url, None, lineno, name))
                name = ""


    def parse_text (self):
        """parse a text file with on url per line; comment and blank
           lines are ignored
           UNUSED and UNTESTED, just use linkchecker `cat file.txt`
        """
        lineno = 0
        lines = self.getContent().splitlines()
        for line in lines:
            lineno += 1
            line = line.strip()
            if not line or line.startswith('#'): continue
            self.config.appendUrl(GetUrlDataFrom(line, self.recursionLevel+1,
                                  self.config, self.url, None, lineno, ""))


    def parse_css (self):
        """parse a CSS file for url() patterns"""
        lineno = 0
        lines = self.getContent().splitlines()
        for line in lines:
            lineno += 1
            # XXX todo: css url pattern matching


    def __str__ (self):
        return ("%s link\n"
	       "urlname=%s\n"
	       "parentName=%s\n"
	       "baseRef=%s\n"
	       "cached=%s\n"
	       "recursionLevel=%s\n"
	       "urlConnection=%s\n"
	       "line=%s\n"
               "column=%s\n"
	       "name=%s" % \
             (self.scheme, self.urlName, self.parentName, self.baseRef,
              self.cached, self.recursionLevel, self.urlConnection, self.line,
              self.column, self.name))

