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

import sys
import os
import re
import urlparse
import urllib2
import urllib
import time
import traceback
import socket
import select
import linkcheck
import bk.log
import bk.i18n


ws_at_start_or_end = re.compile(r"(^\s+)|(\s+$)").search

# helper function for internal errors
def internal_error ():
    print >>sys.stderr, bk.i18n._("""\n********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
1) The URL or file you are testing
2) Your commandline arguments and/or configuration.
3) The system information below.

If you disclose some information because its too private to you thats ok.
I will try to help you nontheless (but you have to give me *something*
I can work with ;).
""") % linkcheck.Config.Email
    etype, value = sys.exc_info()[:2]
    print >>sys.stderr, etype, value
    traceback.print_exc()
    print_app_info()
    print >>sys.stderr, bk.i18n._("\n******** LinkChecker internal error, bailing out ********")
    sys.exit(1)


def print_app_info ():
    print >>sys.stderr, bk.i18n._("System info:")
    print >>sys.stderr, linkcheck.Config.App
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


# regular expression for port numbers
is_valid_port = re.compile(r"\d+").match


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
        self.errorString = bk.i18n._("Error")
        self.validString = bk.i18n._("Valid")
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
        self.errorString = bk.i18n._("Error")+": "+s

    def setValid (self, s):
        self.valid = True
        self.validString = bk.i18n._("Valid")+": "+s

    def isParseable (self):
        return False

    def isHtml (self):
        return False

    def isHttp (self):
        return False

    def isFile (self):
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
        """fill attributes from cache data"""
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
        """return all data values that should be put in the cache"""
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
        self.url = urllib.unquote(self.url)
        # split into (modifiable) list
        self.urlparts = list(urlparse.urlsplit(self.url))
        # check userinfo@host:port syntax
        self.userinfo, host = urllib.splituser(self.urlparts[1])
        x, port = urllib.splitport(host)
        if port is not None and not is_valid_port(port):
            raise linkcheck.LinkCheckerError(bk.i18n._("URL has invalid port number %r")\
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
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            etype, value = sys.exc_info()[:2]
            if etype!=4:
                raise
        except (KeyboardInterrupt, linkcheck.test_support.Error):
            raise
        except:
            internal_error()

    def _check (self):
        debug(BRING_IT_ON, "Checking", self)
        if self.recursionLevel and self.config['wait']:
            debug(BRING_IT_ON, "sleeping for", self.config['wait'], "seconds")
            time.sleep(self.config['wait'])
        t = time.time()
        if not self.checkCache():
            return
        # apply filter
        debug(BRING_IT_ON, "extern =", self.extern)
        if self.extern[0] and (self.config["strict"] or self.extern[1]):
            self.setWarning(
                  bk.i18n._("outside of domain filter, checked only syntax"))
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
                evalue = bk.i18n._('Hostname not found')
            # make nicer error msg for bad status line
            if isinstance(evalue, linkcheck.httplib2.BadStatusLine):
                evalue = bk.i18n._('Bad HTTP response %r')%str(evalue)
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
            self.setError(bk.i18n._("could not parse content: %r")%str(value))
        # close
        self.closeConnection()
        self.logMe()
        debug(BRING_IT_ON, "caching")
        self.putInCache()

    def checkSyntax (self):
        debug(BRING_IT_ON, "checking syntax")
        if not self.urlName or self.urlName=="":
            self.setError(bk.i18n._("URL is null or empty"))
            self.logMe()
            return False
        if ws_at_start_or_end(self.urlName):
            self.setError(bk.i18n._("URL has whitespace at beginning or end"))
            self.logMe()
            return False
        try:
	    self.buildUrl()
            self.extern = self._getExtern()
        except linkcheck.LinkCheckerError, msg:
            self.setError(str(msg))
            self.logMe()
            return False
        return True

    def checkCache (self):
        debug(BRING_IT_ON, "checking cache")
        for key in self.getCacheKeys():
            if self.config.urlCache_has_key(key):
                self.copyFromCache(self.config.urlCache_get(key))
                self.cached = True
                self.logMe()
                return False
        return True

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
               not self.isCached() and \
               (self.config["recursionlevel"] < 0 or
                self.recursionLevel < self.config["recursionlevel"]) and \
               not self.extern[0] and self.contentAllowsRobots()

    def contentAllowsRobots (self):
        if not self.isHtml():
            return True
        if not (self.isHttp() or self.isFile()):
            return True
        h = linkcheck.linkparse.MetaRobotsFinder(self.getContent())
        p = bk.HtmlParser.htmlsax.parser(h)
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
        h = linkcheck.linkparse.LinkFinder(self.getContent(), tags={'a': ['name'], None: ['id']})
        p = bk.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        for cur_anchor,line,column,name,base in h.urls:
            if cur_anchor == self.anchor:
                return
        self.setWarning(bk.i18n._("anchor #%s not found") % self.anchor)

    def _getExtern (self):
        if not (self.config["externlinks"] or self.config["internlinks"]):
            return (0, 0)
        # deny and allow external checking
        bk.log.debug(HURT_ME_PLENTY, "Url", self.url)
        if self.config["denyallow"]:
            for entry in self.config["externlinks"]:
                bk.log.debug(HURT_ME_PLENTY, "Extern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            for entry in self.config["internlinks"]:
                bk.log.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            return (0, 0)
        else:
            for entry in self.config["internlinks"]:
                bk.log.debug(HURT_ME_PLENTY, "Intern entry", entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            for entry in self.config["externlinks"]:
                bk.log.debug(HURT_ME_PLENTY, "Extern entry", entry)
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
            self.setWarning(bk.i18n._("Found %r in link contents")%match.group())

    def checkSize (self):
        """if a maximum size was given, call this function to check it
           against the content size of this url"""
        maxbytes = self.config["warnsizebytes"]
        if maxbytes is not None and self.dlsize >= maxbytes:
            self.setWarning(bk.i18n._("Content size %s is larger than %s")%\
                         (linkcheck.StringUtil.strsize(self.dlsize),
                          linkcheck.StringUtil.strsize(maxbytes)))

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
        h = linkcheck.linkparse.LinkFinder(self.getContent(), tags={'base': ['href']})
        p = bk.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.getContent())
        p.flush()
        h.parser = None
        p.handler = None
        baseRef = None
        if len(h.urls)>=1:
            baseRef = h.urls[0][0]
            if len(h.urls)>1:
                self.setWarning(bk.i18n._(
                "more than one <base> tag found, using only the first one"))
        h = linkcheck.linkparse.LinkFinder(self.getContent())
        p = bk.HtmlParser.htmlsax.parser(h)
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
            debug(NIGHTMARE, "Put url %r in queue"%url)
            self.config.appendUrl(linkcheck.checker.getUrlDataFrom(url,
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
                    self.config.appendUrl(linkcheck.checker.getUrlDataFrom(url,
           self.recursionLevel+1, self.config, self.url, None, lineno, name))
                name = ""

    def parse_text (self):
        """parse a text file with on url per line; comment and blank
           lines are ignored
           UNUSED and UNTESTED, just use linkchecker `cat file.txt`
        """
        lineno = 0
        for line in self.getContent().splitlines():
            lineno += 1
            line = line.strip()
            if not line or line.startswith('#'): continue
            self.config.appendUrl(linkcheck.checker.getUrlDataFrom(line, self.recursionLevel+1,
                               self.config, parentName=self.url, line=lineno))

    def parse_css (self):
        """parse a CSS file for url() patterns"""
        lineno = 0
        for line in self.getContent().splitlines():
            lineno += 1
            for mo in linkcheck.linkparse.css_url_re.finditer(line):
                column = mo.start("url")
                self.config.appendUrl(linkcheck.checker.getUrlDataFrom(mo.group("url"),
                      self.recursionLevel+1, self.config,
                      parentName=self.url, line=lineno, column=column))

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

