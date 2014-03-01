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
Robots.txt parser.

The robots.txt Exclusion Protocol is implemented as specified in
http://www.robotstxt.org/wc/norobots-rfc.html
"""
import urlparse
import urllib
import time
import requests
from . import log, LOG_CHECK, configuration

__all__ = ["RobotFileParser"]

ACCEPT_ENCODING = 'x-gzip,gzip,deflate'

class RobotFileParser (object):
    """This class provides a set of methods to read, parse and answer
    questions about a single robots.txt file."""

    def __init__ (self, url='', proxy=None, user=None, password=None):
        """Initialize internal entry lists and store given url and
        credentials."""
        self.set_url(url)
        self.proxy = proxy
        self.user = user
        self.password = password
        self._reset()

    def _reset (self):
        """Reset internal flags and entry lists."""
        self.entries = []
        self.default_entry = None
        self.disallow_all = False
        self.allow_all = False
        self.last_checked = 0
        # list of tuples (sitemap url, line number)
        self.sitemap_urls = []

    def mtime (self):
        """Returns the time the robots.txt file was last fetched.

        This is useful for long-running web spiders that need to
        check for new robots.txt files periodically.

        @return: last modified in time.time() format
        @rtype: number
        """
        return self.last_checked

    def modified (self):
        """Set the time the robots.txt file was last fetched to the
        current time."""
        self.last_checked = time.time()

    def set_url (self, url):
        """Set the URL referring to a robots.txt file."""
        self.url = url
        self.host, self.path = urlparse.urlparse(url)[1:3]

    def read (self):
        """Read the robots.txt URL and feeds it to the parser."""
        self._reset()
        headers = {
            'User-Agent': configuration.UserAgent,
            'Accept-Encoding': ACCEPT_ENCODING,
        }
        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get('content-type')
            if content_type and content_type.lower().startswith('text/plain'):
                self.parse(response.iter_lines())
            else:
                log.debug(LOG_CHECK, "%r allow all (no text content)", self.url)
                self.allow_all = True
        except requests.HTTPError, x:
            if x.response.status_code in (401, 403):
                self.disallow_all = True
                log.debug(LOG_CHECK, "%r disallow all (code %d)", self.url, x.response.status_code)
            else:
                self.allow_all = True
                log.debug(LOG_CHECK, "%r allow all (HTTP error)", self.url)
        except requests.exceptions.Timeout:
            raise
        except requests.exceptions.RequestException:
            # no network or other failure
            self.allow_all = True
            log.debug(LOG_CHECK, "%r allow all (request error)", self.url)

    def _add_entry (self, entry):
        """Add a parsed entry to entry list.

        @return: None
        """
        if "*" in entry.useragents:
            # the default entry is considered last
            self.default_entry = entry
        else:
            self.entries.append(entry)

    def parse (self, lines):
        """Parse the input lines from a robot.txt file.
        We allow that a user-agent: line is not preceded by
        one or more blank lines.

        @return: None
        """
        log.debug(LOG_CHECK, "%r parse lines", self.url)
        state = 0
        linenumber = 0
        entry = Entry()

        for line in lines:
            line = line.strip()
            linenumber += 1
            if not line:
                if state == 1:
                    log.debug(LOG_CHECK, "%r line %d: allow or disallow directives without any user-agent line", self.url, linenumber)
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
                        log.debug(LOG_CHECK, "%r line %d: missing blank line before user-agent directive", self.url, linenumber)
                        self._add_entry(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                elif line[0] == "disallow":
                    if state == 0:
                        log.debug(LOG_CHECK, "%r line %d: missing user-agent directive before this line", self.url, linenumber)
                        pass
                    else:
                        entry.rulelines.append(RuleLine(line[1], False))
                        state = 2
                elif line[0] == "allow":
                    if state == 0:
                        log.debug(LOG_CHECK, "%r line %d: missing user-agent directive before this line", self.url, linenumber)
                        pass
                    else:
                        entry.rulelines.append(RuleLine(line[1], True))
                        state = 2
                elif line[0] == "crawl-delay":
                    if state == 0:
                        log.debug(LOG_CHECK, "%r line %d: missing user-agent directive before this line", self.url, linenumber)
                        pass
                    else:
                        try:
                            entry.crawldelay = max(0, int(line[1]))
                            state = 2
                        except (ValueError, OverflowError):
                            log.debug(LOG_CHECK, "%r line %d: invalid delay number %r", self.url, linenumber, line[1])
                            pass
                elif line[0] == "sitemap":
                    # Note that sitemap URLs must be absolute according to
                    # http://www.sitemaps.org/protocol.html#submit_robots
                    # But this should be checked by the calling layer.
                    self.sitemap_urls.append((line[1], linenumber))
                else:
                    log.debug(LOG_CHECK, "%r line %d: unknown key %r", self.url, linenumber, line[0])
                    pass
            else:
                log.debug(LOG_CHECK, "%r line %d: malformed line %r", self.url, linenumber, line)
                pass
        if state in (1, 2):
            self.entries.append(entry)
        self.modified()
        log.debug(LOG_CHECK, "Parsed rules:\n%s", str(self))

    def can_fetch (self, useragent, url):
        """Using the parsed robots.txt decide if useragent can fetch url.

        @return: True if agent can fetch url, else False
        @rtype: bool
        """
        log.debug(LOG_CHECK, "%r check allowance for:\n  user agent: %r\n  url: %r ...", self.url, useragent, url)
        if not isinstance(useragent, str):
            useragent = useragent.encode("ascii", "ignore")
        if not isinstance(url, str):
            url = url.encode("ascii", "ignore")
        if self.disallow_all:
            log.debug(LOG_CHECK, " ... disallow all.")
            return False
        if self.allow_all:
            log.debug(LOG_CHECK, " ... allow all.")
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
        log.debug(LOG_CHECK, " ... agent not found, allow.")
        return True

    def get_crawldelay (self, useragent):
        """Look for a configured crawl delay.

        @return: crawl delay in seconds or zero
        @rtype: integer >= 0
        """
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.crawldelay
        return 0

    def __str__ (self):
        """Constructs string representation, usable as contents of a
        robots.txt file.

        @return: robots.txt format
        @rtype: string
        """
        lines = [str(entry) for entry in self.entries]
        if self.default_entry is not None:
            lines.append(str(self.default_entry))
        return "\n\n".join(lines)


class RuleLine (object):
    """A rule line is a single "Allow:" (allowance==1) or "Disallow:"
    (allowance==0) followed by a path.
    """

    def __init__ (self, path, allowance):
        """Initialize with given path and allowance info."""
        if path == '' and not allowance:
            # an empty value means allow all
            allowance = True
            path = '/'
        self.path = urllib.quote(path)
        self.allowance = allowance

    def applies_to (self, path):
        """Look if given path applies to this rule.

        @return: True if pathname applies to this rule, else False
        @rtype: bool
        """
        return self.path == "*" or path.startswith(self.path)

    def __str__ (self):
        """Construct string representation in robots.txt format.

        @return: robots.txt format
        @rtype: string
        """
        return ("Allow" if self.allowance else "Disallow")+": "+self.path


class Entry (object):
    """An entry has one or more user-agents and zero or more rulelines."""

    def __init__ (self):
        """Initialize user agent and rule list."""
        self.useragents = []
        self.rulelines = []
        self.crawldelay = 0

    def __str__ (self):
        """string representation in robots.txt format.

        @return: robots.txt format
        @rtype: string
        """
        lines = ["User-agent: %s" % agent for agent in self.useragents]
        if self.crawldelay:
            lines.append("Crawl-delay: %d" % self.crawldelay)
        lines.extend([str(line) for line in self.rulelines])
        return "\n".join(lines)

    def applies_to (self, useragent):
        """Check if this entry applies to the specified agent.

        @return: True if this entry applies to the agent, else False.
        @rtype: bool
        """
        if not useragent:
            return True
        useragent = useragent.lower()
        for agent in self.useragents:
            if agent == '*':
                # we have the catch-all agent
                return True
            if agent.lower() in useragent:
                return True
        return False

    def allowance (self, filename):
        """Preconditions:
        - our agent applies to this entry
        - filename is URL decoded

        Check if given filename is allowed to acces this entry.

        @return: True if allowed, else False
        @rtype: bool
        """
        for line in self.rulelines:
            log.debug(LOG_CHECK, "%s %s %s", filename, str(line), line.allowance)
            if line.applies_to(filename):
                log.debug(LOG_CHECK, " ... rule line %s", line)
                return line.allowance
        log.debug(LOG_CHECK, " ... no rule lines of %s applied to %s; allowed.", self.useragents, filename)
        return True
