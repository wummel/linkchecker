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
import linkcheck.linkparse
import linkcheck.containers
import linkcheck.log
import linkcheck.httplib2
import linkcheck.HtmlParser.htmlsax

from linkcheck.i18n import _


ws_at_start_or_end = re.compile(r"(^\s+)|(\s+$)").search


def internal_error ():
    """print internal error message to stderr"""
    print >> sys.stderr, os.linesep
    print >> sys.stderr, _("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
1) The URL or file you are testing
2) Your commandline arguments and/or configuration.
3) The system information below.

If you disclose some information because its too private to you thats ok.
I will try to help you nontheless (but you have to give me *something*
I can work with ;).
""") % linkcheck.configuration.Email
    etype, value = sys.exc_info()[:2]
    print >> sys.stderr, etype, value
    traceback.print_exc()
    print_app_info()
    print >> sys.stderr, os.linesep, \
            _("******** LinkChecker internal error, bailing out ********")
    sys.exit(1)


def print_app_info ():
    """print system and application info to stderr"""
    print >> sys.stderr, _("System info:")
    print >> sys.stderr, linkcheck.configuration.App
    print >> sys.stderr, _("Python %s on %s") % (sys.version, sys.platform)
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> sys.stderr, key, "=", repr(value)


class UrlBase (object):
    """An URL with additional information like validity etc."""

    def __init__ (self, base_url, recursion_level, config,
                  parent_url = None, base_ref = None,
                  line = 0, column = 0, name = ""):
        """Initialize check data, and store given variables.

           @base_url - quoted url
           @recursion_level - on what check level lies the base url
           @config - Configuration instance
           @parent_url - quoted url of parent or None
           @base_ref - quoted url of <base href> or None
           @line - line number of url in parent content
           @column - column number of url in parent content
           @name - name of url or empty
        """
        self.base_ref = base_ref
        self.base_url = base_url
        self.url = None
        self.urlparts = None
        self.parent_url = parent_url
        self.anchor = None
        self.recursion_level = recursion_level
        self.config = config
        self.result = ""
        self.valid = True
        self.warning = linkcheck.containers.SetList()
        self.info = linkcheck.containers.SetList()
        self.line = line
        self.column = column
        self.name = name
        self.dltime = -1
        self.dlsize = -1
        self.checktime = 0
        self.cached = False
        self.url_connection = None
        self.extern = (1, 0)
        self.data = None
        self.has_content = False
        if linkcheck.url.url_needs_quoting(self.base_url):
            self.add_warning(_("Base URL is not properly quoted"))
            self.base_url = linkcheck.url.url_norm(self.base_url)
        if self.base_ref and linkcheck.url.url_needs_quoting(self.base_ref):
            self.add_warning(_("Base reference is not properly quoted"))
            self.base_ref = linkcheck.url.url_norm(self.base_ref)
        if self.parent_url and linkcheck.url.url_needs_quoting(self.parent_url):
            self.add_warning(_("Parent url is not properly quoted"))
            self.parent_url = linkcheck.url.url_norm(self.parent_url)
        url = linkcheck.checker.absolute_url(base_url, base_ref, parent_url)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0] or "file"

    def set_result (self, msg, valid=True):
        """set result string and validity"""
        fmt = {'result': msg}
        if valid:
            self.result = _("Valid: %(result)s") % fmt
        else:
            self.result = _("Error: %(result)s") % fmt
        self.valid = valid

    def is_parseable (self):
        """return True iff content of this url is parseable"""
        return False

    def is_html (self):
        """return True iff content of this url is HTML formatted"""
        return False

    def is_http (self):
        """return True for http:// urls"""
        return False

    def is_file (self):
        """return True for file:// urls"""
        return False

    def add_warning (self, s):
        """add a warning string"""
        self.warning.append(s)

    def add_info (self, s):
        """add an info string"""
        self.info.append(s)

    def copy_from_cache (self, cache_data):
        """fill attributes from cache data"""
        self.result = cache_data["result"]
        self.warning.extend(cache_data["warning"])
        self.info.extend(cache_data["info"])
        self.valid = cache_data["valid"]
        self.dltime = cache_data["dltime"]

    def get_cache_data (self):
        """return all data values that should be put in the cache"""
        return {"result": self.result,
                "warning": self.warning,
                "info": self.info,
                "valid": self.valid,
                "dltime": self.dltime,
               }

    def get_cache_keys (self):
        key = self.get_cache_key()
        if key is None:
            return []
        return [key]

    def is_cached (self):
        key = self.get_cache_key()
        return self.cached or self.config.url_seen_has_key(key)

    def get_cache_key (self):
        # note: the host is already lowercase
        if self.urlparts:
            if self.config["anchorcaching"]:
                # do not ignore anchor
                return urlparse.urlunsplit(self.urlparts)
            else:
                # removed anchor from cache key
                return urlparse.urlunsplit(self.urlparts[:4]+[''])
        return None

    def put_in_cache (self):
        """put url data into cache"""
        if self.is_cached():
            # another thread was faster and cached this url already
            return
        data = self.get_cache_data()
        for key in self.get_cache_keys():
            self.config.url_cache_set(key, data)
            self.config.url_seen_set(key)

    def build_url (self):
        # make url absolute
        if self.base_ref:
            # use base reference as parent url
            if ":" not in self.base_ref:
                # some websites have a relative base reference
                self.base_ref = urlparse.urljoin(self.parent_url,
                                                 self.base_ref)
            self.url = urlparse.urljoin(self.base_ref, self.base_url)
        elif self.parent_url:
            self.url = urlparse.urljoin(self.parent_url, self.base_url)
        else:
            self.url = self.base_url
        # split into (modifiable) list
        self.urlparts = list(urlparse.urlsplit(self.url))
        # check userinfo@host:port syntax
        self.userinfo, host = urllib.splituser(self.urlparts[1])
        x, port = urllib.splitport(host)
        if port is not None and not linkcheck.url.is_numeric_port(port):
            raise linkcheck.LinkCheckerError(_("URL has invalid port %r") %\
                                             str(port))
        # set host lowercase and without userinfo
        self.urlparts[1] = host.lower()
        # safe anchor for later checking
        self.anchor = self.urlparts[4]

    def log_me (self):
        """announce the url data as checked to the configured loggers"""
        linkcheck.log.debug(linkcheck.LOG_CHECK, "logging url")
        self.config.increment_linknumber()
        if self.config["verbose"] or not self.valid or \
           (self.warning and self.config["warnings"]):
            self.config.logger_new_url(self)

    def check (self):
        try:
            self.local_check()
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            etype, value = sys.exc_info()[:2]
            if etype != 4:
                raise
        except KeyboardInterrupt:
            raise
        except:
            internal_error()

    def local_check (self):
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Checking %s", self)
        if self.recursion_level and self.config['wait']:
            linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "sleeping for %d seconds", self.config['wait'])
            time.sleep(self.config['wait'])
        t = time.time()
        if not self.check_cache():
            return
        # apply filter
        linkcheck.log.debug(linkcheck.LOG_CHECK, "extern=%s", self.extern)
        if self.extern[0] and (self.config["strict"] or self.extern[1]):
            self.add_warning(
                  _("outside of domain filter, checked only syntax"))
            self.log_me()
            return

        # check connection
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking connection")
        try:
            self.check_connection()
            if self.cached:
                return
            if self.config["anchors"]:
                self.check_anchors()
        except tuple(linkcheck.checker.ExcList):
            etype, evalue, etb = sys.exc_info()
            linkcheck.log.debug(linkcheck.LOG_CHECK, "exception %s",
                                traceback.format_tb(etb))
            # make nicer error msg for unknown hosts
            if isinstance(evalue, socket.error) and evalue[0]==-2:
                evalue = _('Hostname not found')
            # make nicer error msg for bad status line
            if isinstance(evalue, linkcheck.httplib2.BadStatusLine):
                evalue = _('Bad HTTP response %r')%str(evalue)
            self.set_result(str(evalue), valid=False)

        # check content
        warningregex = self.config["warningregex"]
        if warningregex and self.valid:
            linkcheck.log.debug(linkcheck.LOG_CHECK, "checking content")
            try:
                self.check_content(warningregex)
            except tuple(linkcheck.checker.ExcList):
                value, tb = sys.exc_info()[1:]
                linkcheck.log.debug(linkcheck.LOG_CHECK, "exception %s",
                                    traceback.format_tb(tb))
                self.set_result(str(value), valid=False)

        self.checktime = time.time() - t
        # check recursion
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking recursion")
        try:
            if self.allows_recursion():
                self.parse_url()
            # check content size
            self.check_size()
        except tuple(linkcheck.checker.ExcList):
            value, tb = sys.exc_info()[1:]
            linkcheck.log.debug(linkcheck.LOG_CHECK, "exception %s",
                                traceback.format_tb(tb))
            self.set_result(_("could not parse content: %r") % str(value),
                            valid=False)
        # close
        self.close_connection()
        self.log_me()
        linkcheck.log.debug(linkcheck.LOG_CHECK, "caching")
        self.put_in_cache()

    def check_syntax (self):
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking syntax")
        if not self.base_url:
            self.set_result(_("URL is empty"), valid=False)
            self.log_me()
            return False
        if ws_at_start_or_end(self.base_url):
            self.set_result(_("URL has whitespace at beginning or end"),
                            valid=False)
            self.log_me()
            return False
        try:
            self.build_url()
            self.extern = self._get_extern()
        except linkcheck.LinkCheckerError, msg:
            self.set_result(str(msg), valid=False)
            self.log_me()
            return False
        return True

    def check_cache (self):
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking cache")
        for key in self.get_cache_keys():
            if self.config.url_cache_has_key(key):
                self.copy_from_cache(self.config.url_cache_get(key))
                self.cached = True
                self.log_me()
                return False
        return True

    def close_connection (self):
        """close an opened url connection"""
        # brute force closing
        if self.url_connection is not None:
            try:
                self.url_connection.close()
            except:
                # ignore close errors
                pass
            # release variable for garbage collection
            self.url_connection = None

    def check_connection (self):
        self.url_connection = urllib2.urlopen(self.url)

    def allows_recursion (self):
        """return True iff we can recurse into the url's content"""
        # note: test self.valid before self.is_parseable()
        return self.valid and \
            self.is_parseable() and \
            self.can_get_content() and \
            not self.is_cached() and \
            (self.config["recursionlevel"] < 0 or
             self.recursion_level < self.config["recursionlevel"]) and \
            not self.extern[0] and self.content_allows_robots()

    def content_allows_robots (self):
        if not self.is_html():
            return True
        if not (self.is_http() or self.is_file()):
            return True
        h = linkcheck.linkparse.MetaRobotsFinder(self.get_content())
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.get_content())
        p.flush()
        h.parser = None
        p.handler = None
        return h.follow

    def check_anchors (self):
        if not (self.valid and self.anchor and self.is_html() and \
                self.can_get_content()):
            # do not bother
            return
        linkcheck.log.debug(linkcheck.LOG_CHECK, "checking anchor %r",
                            self.anchor)
        h = linkcheck.linkparse.LinkFinder(self.get_content(),
                                   tags={'a': ['name'], None: ['id']})
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.get_content())
        p.flush()
        h.parser = None
        p.handler = None
        for cur_anchor, line, column, name, base in h.urls:
            if cur_anchor == self.anchor:
                return
        self.add_warning(_("anchor #%s not found") % self.anchor)

    def _get_extern (self):
        if not (self.config["externlinks"] or self.config["internlinks"]):
            return (0, 0)
        # deny and allow external checking
        linkcheck.log.debug(linkcheck.LOG_CHECK, "Url %r", self.url)
        if self.config["denyallow"]:
            for entry in self.config["externlinks"]:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Extern entry %r",
                                    entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            for entry in self.config["internlinks"]:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Intern entry %r",
                                    entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            return (0, 0)
        else:
            for entry in self.config["internlinks"]:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Intern entry %r",
                                    entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (0, 0)
            for entry in self.config["externlinks"]:
                linkcheck.log.debug(linkcheck.LOG_CHECK, "Extern entry %r",
                                    entry)
                match = entry['pattern'].search(self.url)
                if (entry['negate'] and not match) or \
                   (match and not entry['negate']):
                    return (1, entry['strict'])
            return (1, 0)

    def can_get_content (self):
        """indicate wether url get_content() can be called"""
        return True

    def get_content (self):
        """Precondition: url_connection is an opened URL."""
        if not self.has_content:
            t = time.time()
            self.data = self.url_connection.read()
            self.dltime = time.time() - t
            self.dlsize = len(self.data)
            self.has_content = True
        return self.data

    def check_content (self, warningregex):
        """If a warning expression was given, call this function to check it
           against the content of this url.
        """
        if not self.can_get_content():
            return
        match = warningregex.search(self.get_content())
        if match:
            self.add_warning(_("Found %r in link contents") % match.group())

    def check_size (self):
        """if a maximum size was given, call this function to check it
           against the content size of this url"""
        maxbytes = self.config["warnsizebytes"]
        if maxbytes is not None and self.dlsize >= maxbytes:
            self.add_warning(_("Content size %s is larger than %s") % \
                         (linkcheck.strformat.strsize(self.dlsize),
                          linkcheck.strformat.strsize(maxbytes)))

    def parse_url (self):
        """Parse url content and search for recursive links.
           Default parse type is html.
        """
        linkcheck.log.debug(linkcheck.LOG_CHECK,
                            "Parsing recursively into %s", self)
        self.parse_html()

    def get_user_password (self):
        for auth in self.config["authentication"]:
            if auth['pattern'].match(self.url):
                return auth['user'], auth['password']
        return None, None

    def parse_html (self):
        # search for a possible base reference
        h = linkcheck.linkparse.LinkFinder(self.get_content(),
                                           tags={'base': ['href']})
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.get_content())
        p.flush()
        h.parser = None
        p.handler = None
        base_ref = None
        if len(h.urls)>=1:
            base_ref = h.urls[0][0]
            if len(h.urls)>1:
                self.add_warning(_(
                "more than one <base> tag found, using only the first one"))
        h = linkcheck.linkparse.LinkFinder(self.get_content())
        p = linkcheck.HtmlParser.htmlsax.parser(h)
        h.parser = p
        p.feed(self.get_content())
        p.flush()
        h.parser = None
        p.handler = None
        for s in h.parse_info:
            # the parser had warnings/errors
            self.add_warning(s)
        for url, line, column, name, codebase in h.urls:
            if codebase:
                base = codebase
            else:
                base = base_ref
            linkcheck.log.debug(linkcheck.LOG_CHECK, "Put url %r in queue",
                                url)
            self.config.append_url(linkcheck.checker.get_url_from(url,
                                  self.recursion_level+1, self.config,
                                  parent_url=self.url, base_ref=base,
                                  line=line, column=column, name=name))

    def parse_opera (self):
        """parse an opera bookmark file"""
        name = ""
        lineno = 0
        lines = self.get_content().splitlines()
        for line in lines:
            lineno += 1
            line = line.strip()
            if line.startswith("NAME="):
                name = line[5:]
            elif line.startswith("URL="):
                url = line[4:]
                if url:
                    self.config.append_url(linkcheck.checker.get_url_from(url,
           self.recursion_level+1, self.config, self.url, None, lineno, name))
                name = ""

    def parse_text (self):
        """parse a text file with on url per line; comment and blank
           lines are ignored
           UNUSED and UNTESTED, just use linkchecker `cat file.txt`
        """
        lineno = 0
        for line in self.get_content().splitlines():
            lineno += 1
            line = line.strip()
            if not line or line.startswith('#'): continue
            self.config.append_url(
                  linkcheck.checker.get_url_from(line, self.recursion_level+1,
                               self.config, parent_url=self.url, line=lineno))

    def parse_css (self):
        """parse a CSS file for url() patterns"""
        lineno = 0
        for line in self.get_content().splitlines():
            lineno += 1
            for mo in linkcheck.linkparse.css_url_re.finditer(line):
                column = mo.start("url")
                self.config.append_url(
                             linkcheck.checker.get_url_from(mo.group("url"),
                             self.recursion_level+1, self.config,
                             parent_url=self.url, line=lineno, column=column))

    def __str__ (self):
        """return serialized url check data"""
        return os.linesep.join([
            "%s link" % self.scheme,
            "base_url=%s" % self.base_url,
            "parent_url=%s" % self.parent_url,
            "base_ref=%s" % self.base_ref,
            "cached=%s" % self.cached,
            "recursion_level=%s" % self.recursion_level,
            "url_connection=%s" % self.url_connection,
            "line=%s" % self.line,
            "column=%s" % self.column,
            "name=%s" % self.name,
           ])
