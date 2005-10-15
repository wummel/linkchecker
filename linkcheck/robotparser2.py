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
Robots.txt parser.

The robots.txt Exclusion Protocol is implemented as specified in
http://www.robotstxt.org/wc/norobots-rfc.html
"""

import urlparse
import httplib
import urllib
import urllib2
import time
import socket
import re
import sys
import zlib
import gzip
import cStringIO as StringIO
import linkcheck
import linkcheck.configuration
import linkcheck.log

__all__ = ["RobotFileParser"]


class PasswordManager (object):
    """
    Simple password manager storing username and password. Suitable
    for use as an AuthHandler instance in urllib2.
    """

    def __init__ (self, user, password):
        """
        Store given username and password.
        """
        self.user = user
        self.password = password

    def add_password (self, realm, uri, user, passwd):
        """
        Does nothing since username and password are already stored.

        @return: None
        """
        pass

    def find_user_password (self, realm, authuri):
        """
        Get stored username and password.

        @return: A tuple (user, password)
        @rtype: tuple
        """
        return self.user, self.password


class RobotFileParser (object):
    """
    This class provides a set of methods to read, parse and answer
    questions about a single robots.txt file.
    """

    def __init__ (self, url='', user=None, password=None):
        """
        Initialize internal entry lists and store given url and
        credentials.
        """
        self.set_url(url)
        self.user = user
        self.password = password
        self._reset()

    def _reset (self):
        """
        Reset internal flags and entry lists.

        @return: None
        """
        self.entries = []
        self.default_entry = None
        self.disallow_all = False
        self.allow_all = False
        self.last_checked = 0

    def mtime (self):
        """
        Returns the time the robots.txt file was last fetched.

        This is useful for long-running web spiders that need to
        check for new robots.txt files periodically.

        @return: last modified in time.time() format
        @rtype: number
        """
        return self.last_checked

    def modified (self):
        """
        Sets the time the robots.txt file was last fetched to the
        current time.

        @return: None
        """
        self.last_checked = time.time()

    def set_url (self, url):
        """
        Sets the URL referring to a robots.txt file.

        @return: None
        """
        self.url = url
        self.host, self.path = urlparse.urlparse(url)[1:3]

    def get_opener (self):
        """
        Construct an URL opener object. It considers the given credentials
        from the __init__() method and supports proxies.

        @return: URL opener
        @rtype: urllib2.OpenerDirector
        """
        pwd_manager = PasswordManager(self.user, self.password)
        handlers = [
            urllib2.ProxyHandler(urllib.getproxies()),
            urllib2.UnknownHandler,
            HttpWithGzipHandler,
            urllib2.HTTPBasicAuthHandler(pwd_manager),
            urllib2.ProxyBasicAuthHandler(pwd_manager),
            urllib2.HTTPDigestAuthHandler(pwd_manager),
            urllib2.ProxyDigestAuthHandler(pwd_manager),
            urllib2.HTTPDefaultErrorHandler,
            urllib2.HTTPRedirectHandler,
        ]
        if hasattr(httplib, 'HTTPS'):
            handlers.append(HttpsWithGzipHandler)
        return urllib2.build_opener(*handlers)

    def read (self):
        """
        Reads the robots.txt URL and feeds it to the parser.

        @return: None
        """
        self._reset()
        headers = {
            'User-Agent': linkcheck.configuration.UserAgent,
            'Accept-Encoding' : 'gzip;q=1.0, deflate;q=0.9, identity;q=0.5',
        }
        req = urllib2.Request(self.url, None, headers)
        try:
            self._read_content(req)
        except urllib2.HTTPError, x:
            if x.code in (401, 403):
                self.disallow_all = True
                linkcheck.log.debug(linkcheck.LOG_CHECK,
                                    "%s disallow all", self.url)
            else:
                self.allow_all = True
                linkcheck.log.debug(linkcheck.LOG_CHECK,
                                    "%s allow all", self.url)
        except (socket.gaierror, socket.error, urllib2.URLError), x:
            # no network
            self.allow_all = True
            linkcheck.log.debug(linkcheck.LOG_CHECK, "%s allow all", self.url)
        except IOError, msg:
            self.allow_all = True
            linkcheck.log.debug(linkcheck.LOG_CHECK, "%s allow all", self.url)
        except httplib.HTTPException:
            self.allow_all = True
            linkcheck.log.debug(linkcheck.LOG_CHECK, "%s allow all", self.url)
        except ValueError:
            # XXX bug workaround:
            # urllib2.AbstractDigestAuthHandler raises ValueError on
            # failed authorisation
            self.disallow_all = True
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                                "%s disallow all", self.url)

    def _read_content (self, req):
        """
        Read robots.txt content.
        @raise: urllib2.HTTPError on HTTP failure codes
        @raise: socket.gaierror, socket.error, urllib2.URLError on network
          errors
        @raise: httplib.HTTPException, IOError on HTTP errors
        @raise: ValueError on bad digest auth (a bug)
        """
        f = self.get_opener().open(req)
        ct = f.info().get("Content-Type")
        if ct and ct.lower().startswith("text/plain"):
            lines = []
            line = f.readline()
            while line:
                lines.append(line.strip())
                line = f.readline()
            self.parse(lines)
        else:
            self.allow_all = True

    def _add_entry (self, entry):
        """
        Add a parsed entry to entry list.

        @return: None
        """
        if "*" in entry.useragents:
            # the default entry is considered last
            self.default_entry = entry
        else:
            self.entries.append(entry)

    def parse (self, lines):
        """
        Parse the input lines from a robot.txt file.
        We allow that a user-agent: line is not preceded by
        one or more blank lines.

        @return: None
        """
        linkcheck.log.debug(linkcheck.LOG_CHECK, "%s parse lines", self.url)
        state = 0
        linenumber = 0
        entry = Entry()

        for line in lines:
            linenumber += 1
            if not line:
                if state == 1:
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                         "%s line %d: allow or disallow directives without" \
                         " any user-agent line", self.url, linenumber)
                    entry = Entry()
                    state = 0
                elif state == 2:
                    self._add_entry(entry)
                    entry = Entry()
                    state = 0
            # remove optional comment and strip line
            i = line.find('#')
            if i >= 0:
                line = line[:i]
            line = line.strip()
            if not line:
                continue
            line = line.split(':', 1)
            if len(line) == 2:
                line[0] = line[0].strip().lower()
                line[1] = urllib.unquote(line[1].strip())
                if line[0] == "user-agent":
                    if state == 2:
                        linkcheck.log.debug(linkcheck.LOG_CHECK,
                          "%s line %d: missing blank line before user-agent" \
                          " directive", linenumber)
                        self._add_entry(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                elif line[0] == "disallow":
                    if state == 0:
                        linkcheck.log.debug(linkcheck.LOG_CHECK,
                          "%s line %d: missing user-agent directive before" \
                          " this line", self.url, linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 0))
                        state = 2
                elif line[0] == "allow":
                    if state == 0:
                        linkcheck.log.debug(linkcheck.LOG_CHECK,
                          "%s line %d: missing user-agent directive before" \
                          " this line", self.url, linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 1))
                else:
                    linkcheck.log.debug(linkcheck.LOG_CHECK,
                             "%s line %d: unknown key %s",
                             self.url, linenumber, line[0])
            else:
                linkcheck.log.debug(linkcheck.LOG_CHECK,
                    "%s line %d: malformed line %s",
                    self.url, linenumber, line)
        if state == 2:
            self.entries.append(entry)
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "Parsed rules:\n%s", str(self))

    def can_fetch (self, useragent, url):
        """
        Using the parsed robots.txt decide if useragent can fetch url.

        @return: True if agent can fetch url, else False
        @rtype: bool
        """
        linkcheck.log.debug(linkcheck.LOG_CHECK,
              "%s check allowance for:\n" \
              "  user agent: %r\n  url: %r", self.url, useragent, url)
        if not isinstance(useragent, str):
            useragent = useragent.encode("ascii", "ignore")
        if not isinstance(url, str):
            url = url.encode("ascii", "ignore")
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        # search for given user agent matches
        # the first match counts
        url = urllib.quote(urlparse.urlparse(urllib.unquote(url))[2]) or "/"
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.allowance(url)
        # try the default entry last
        if self.default_entry is not None:
            return self.default_entry.allowance(url)
        # agent not found ==> access granted
        return True

    def __str__ (self):
        """
        Constructs string representation, usable as contents of a
        robots.txt file.

        @return: robots.txt format
        @rtype: string
        """
        lines = [str(entry) for entry in self.entries]
        if self.default_entry is not None:
            lines.append(str(self.default_entry))
        return "\n\n".join(lines)


class RuleLine (object):
    """
    A rule line is a single "Allow:" (allowance==1) or "Disallow:"
    (allowance==0) followed by a path.
    """

    def __init__ (self, path, allowance):
        """
        Initialize with given path and allowance info.
        """
        if path == '' and not allowance:
            # an empty value means allow all
            allowance = True
        self.path = urllib.quote(path)
        self.allowance = allowance

    def applies_to (self, path):
        """
        Look if given path applies to this rule.

        @return: True if pathname applies to this rule, else False
        @rtype: bool
        """
        return self.path == "*" or path.startswith(self.path)

    def __str__ (self):
        """
        Construct string representation in robots.txt format.

        @return: robots.txt format
        @rtype: string
        """
        return (self.allowance and "Allow" or "Disallow")+": "+self.path


class Entry (object):
    """
    An entry has one or more user-agents and zero or more rulelines.
    """

    def __init__ (self):
        """
        Initialize user agent and rule list.
        """
        self.useragents = []
        self.rulelines = []

    def __str__ (self):
        """
        string representation in robots.txt format.

        @return: robots.txt format
        @rtype: string
        """
        lines = ["User-agent: %r" % agent for agent in self.useragents]
        lines.extend([str(line) for line in self.rulelines])
        return "\n".join(lines)

    def applies_to (self, useragent):
        """
        Check if this entry applies to the specified agent.

        @return: True if this entry applies to the agent, else False.
        @rtype: bool
        """
        # split the name token and make it lower case
        if not useragent:
            return True
        useragent = useragent.split("/")[0].lower()
        for agent in self.useragents:
            if agent == '*':
                # we have the catch-all agent
                return True
            agent = agent.lower()
            if useragent in agent:
                return True
        return False

    def allowance (self, filename):
        """
        Preconditions:
        - our agent applies to this entry
        - filename is URL decoded

        Check if given filename is allowed to acces this entry.

        @return: True if allowed, else False
        @rtype: bool
        """
        for line in self.rulelines:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
               "%s %s %s", filename, str(line), line.allowance)
            if line.applies_to(filename):
                return line.allowance
        return True

###########################################################################
# urlutils.py - Simplified urllib handling
#
#   Written by Chris Lawrence <lawrencc@debian.org>
#   (C) 1999-2002 Chris Lawrence
#
# This program is freely distributable per the following license:
#
##  Permission to use, copy, modify, and distribute this software and its
##  documentation for any purpose and without fee is hereby granted,
##  provided that the above copyright notice appears in all copies and that
##  both that copyright notice and this permission notice appear in
##  supporting documentation.
##
##  I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
##  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I
##  BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
##  DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
##  WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
##  ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
##  SOFTWARE.
def decode (page):
    """
    Gunzip or deflate a compressed page.
    """
    linkcheck.log.debug(linkcheck.LOG_CHECK,
      "robots.txt page info %d %s", page.code, str(page.info()))
    encoding = page.info().get("Content-Encoding")
    if encoding in ('gzip', 'x-gzip', 'deflate'):
        # cannot seek in socket descriptors, so must get content now
        content = page.read()
        try:
            if encoding == 'deflate':
                fp = StringIO.StringIO(zlib.decompress(content))
            else:
                fp = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(content))
        except zlib.error, msg:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                 "uncompressing had error "
                 "%s, assuming non-compressed content", str(msg))
            fp = StringIO.StringIO(content)
        # remove content-encoding header
        headers = httplib.HTTPMessage(StringIO.StringIO(""))
        ceheader = re.compile(r"(?i)content-encoding:")
        for h in page.info().keys():
            if not ceheader.match(h):
                headers[h] = page.info()[h]
        newpage = urllib.addinfourl(fp, headers, page.geturl())
        if hasattr(page, "code"):
            # python 2.4 compatibility
            newpage.code = page.code
        if hasattr(page, "msg"):
            # python 2.4 compatibility
            newpage.msg = page.msg
        page = newpage
    return page


class HttpWithGzipHandler (urllib2.HTTPHandler):
    """
    Support gzip encoding.
    """
    def http_open (self, req):
        """
        Send request and decode answer.
        """
        return decode(urllib2.HTTPHandler.http_open(self, req))


if hasattr(httplib, 'HTTPS'):
    class HttpsWithGzipHandler (urllib2.HTTPSHandler):
        """
        Support gzip encoding.
        """

        def http_open (self, req):
            """
            Send request and decode answer.
            """
            return decode(urllib2.HTTPSHandler.http_open(self, req))

# end of urlutils.py routines
###########################################################################
