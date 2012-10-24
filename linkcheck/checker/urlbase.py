# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2012 Bastian Kleineidam
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
Base URL handler.
"""
import sys
import os
import logging
import urlparse
import urllib2
import urllib
import time
import errno
import socket
import select

from . import absolute_url, StoringHandler, get_url_from
from .. import (log, LOG_CHECK, LOG_CACHE, httputil, httplib2 as httplib,
  strformat, LinkCheckerError, url as urlutil, trace, clamav, winutil, geoip,
  fileutil, get_link_pat)
from ..HtmlParser import htmlsax
from ..htmlutil import linkparse
from ..network import iputil
from .const import (WARN_URL_EFFECTIVE_URL,
    WARN_URL_ERROR_GETTING_CONTENT, WARN_URL_OBFUSCATED_IP,
    WARN_URL_ANCHOR_NOT_FOUND, WARN_URL_WARNREGEX_FOUND,
    WARN_URL_CONTENT_SIZE_TOO_LARGE, WARN_URL_CONTENT_SIZE_ZERO,
    WARN_URL_CONTENT_SIZE_UNEQUAL, WARN_URL_WHITESPACE,
    WARN_URL_TOO_LONG, URL_MAX_LENGTH, URL_WARN_LENGTH,
    WARN_URL_CONTENT_DUPLICATE,
    ExcList, ExcSyntaxList, ExcNoCacheList)

# helper alias
unicode_safe = strformat.unicode_safe

# schemes that are invalid with an empty hostname
scheme_requires_host = ("ftp", "http", "telnet")

def urljoin (parent, url):
    """
    If url is relative, join parent and url. Else leave url as-is.

    @return joined url
    """
    if urlutil.url_is_absolute(url):
        return url
    return urlparse.urljoin(parent, url)


def url_norm (url, encoding=None):
    """Wrapper for url.url_norm() to convert UnicodeError in
    LinkCheckerError."""
    try:
        return urlutil.url_norm(url, encoding=encoding)
    except UnicodeError:
        msg = _("URL has unparsable domain name: %(name)s") % \
            {"name": sys.exc_info()[1]}
        raise LinkCheckerError(msg)


def getXmlText (parent, tag):
    """Return XML content of given tag in parent element."""
    elem = parent.getElementsByTagName(tag)[0]
    # Yes, the DOM standard is awful.
    rc = []
    for node in elem.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


class UrlBase (object):
    """An URL with additional information like validity etc."""

    # file types that can be parsed recursively
    ContentMimetypes = {
        "text/html": "html",
        "application/xhtml+xml": "html",
        # Include PHP file which helps when checking local .php files.
        # It does not harm other URL schemes like HTTP since HTTP servers
        # should not send this content type. They send text/html instead.
        "application/x-httpd-php": "html",
        "text/css": "css",
        "application/x-shockwave-flash": "swf",
        "application/msword": "word",
        "text/plain+linkchecker": "text",
        "text/plain+opera": "opera",
        "text/plain+chromium": "chromium",
        "application/x-plist+safari": "safari",
        "text/vnd.wap.wml": "wml",
    }

    # Set maximum file size for downloaded files in bytes.
    MaxFilesizeBytes = 1024*1024*5

    def __init__ (self, base_url, recursion_level, aggregate,
                  parent_url=None, base_ref=None, line=-1, column=-1,
                  name=u"", url_encoding=None, extern=None):
        """
        Initialize check data, and store given variables.

        @param base_url: unquoted and possibly unnormed url
        @param recursion_level: on what check level lies the base url
        @param aggregate: aggregate instance
        @param parent_url: quoted and normed url of parent or None
        @param base_ref: quoted and normed url of <base href=""> or None
        @param line: line number of url in parent content
        @param column: column number of url in parent content
        @param name: name of url or empty
        @param url_encoding: encoding of URL or None
        @param extern: None or (is_extern, is_strict)
        """
        self.reset()
        self.init(base_ref, base_url, parent_url, recursion_level,
                  aggregate, line, column, name, url_encoding, extern)
        self.check_syntax()
        if recursion_level == 0:
            self.add_intern_pattern()
        self.set_extern(self.url)

    def init (self, base_ref, base_url, parent_url, recursion_level,
              aggregate, line, column, name, url_encoding, extern):
        """
        Initialize internal data.
        """
        self.base_ref = base_ref
        self.base_url = base_url.strip() if base_url else base_url
        self.parent_url = parent_url
        self.recursion_level = recursion_level
        self.aggregate = aggregate
        self.line = line
        self.column = column
        self.name = name
        self.encoding = url_encoding
        self.charset = None
        self.extern = extern
        if self.base_ref:
            assert not urlutil.url_needs_quoting(self.base_ref), \
                   "unquoted base reference URL %r" % self.base_ref
        if self.parent_url:
            assert not urlutil.url_needs_quoting(self.parent_url), \
                   "unquoted parent URL %r" % self.parent_url
        url = absolute_url(self.base_url, base_ref, parent_url)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0].lower() or "file"
        if self.base_url != base_url:
            self.add_warning(_("Leading or trailing whitespace in URL `%(url)s'.") %
                               {"url": base_url}, tag=WARN_URL_WHITESPACE)

    def reset (self):
        """
        Reset all variables to default values.
        """
        # self.url is constructed by self.build_url() out of base_url
        # and (base_ref or parent) as absolute and normed url.
        # This the real url we use when checking so it also referred to
        # as 'real url'
        self.url = None
        # a splitted version of url for convenience
        self.urlparts = None
        # the scheme, host, port and anchor part of url
        self.scheme = self.host = self.port = self.anchor = None
        # list of parsed anchors
        self.anchors = []
        # the result message string and flag
        self.result = u""
        self.has_result = False
        # cached or not
        self.cached = False
        # valid or not
        self.valid = True
        # list of warnings (without duplicates)
        self.warnings = []
        # list of infos
        self.info = []
        # content size
        self.size = -1
        # last modification time of content in HTTP-date format as specified in RFC2616 chapter 3.3.1
        self.modified = None
        # download time
        self.dltime = -1
        # download size
        self.dlsize = -1
        # check time
        self.checktime = 0
        # connection object
        self.url_connection = None
        # data of url content,  (data == None) means no data is available
        self.data = None
        # cache keys, are set by build_url() calling set_cache_keys()
        self.cache_url_key = None
        self.cache_content_key = None
        # extern flags (is_extern, is_strict)
        self.extern = None
        # flag if the result should be cached
        self.caching = True
        # title is either the URL or parsed from content
        self.title = None
        # flag if content should be checked or not
        self.do_check_content = True
        # MIME content type
        self.content_type = None
        # number of URLs in page content
        self.num_urls = 0

    def set_result (self, msg, valid=True, overwrite=False):
        """
        Set result string and validity.
        """
        if self.has_result and not overwrite:
            log.warn(LOG_CHECK,
              "Double result %r (previous %r) for %s", msg, self.result, self)
        else:
            self.has_result = True
        if not isinstance(msg, unicode):
            log.warn(LOG_CHECK, "Non-unicode result for %s: %r", self, msg)
        elif not msg:
            log.warn(LOG_CHECK, "Empty result for %s", self)
        self.result = msg
        self.valid = valid

    def get_title (self):
        """Return title of page the URL refers to.
        This is per default the filename or the URL."""
        if self.title is None:
            url = u""
            if self.base_url:
                url = self.base_url
            elif self.url:
                url = self.url
            self.title = url
            if "/" in url:
                title = url.rsplit("/", 1)[1]
                if title:
                    self.title = title
        return self.title

    def set_title_from_content (self):
        """Set title of page the URL refers to.from page content."""
        if not self.valid:
            return
        try:
            handler = linkparse.TitleFinder()
        except tuple(ExcList):
            return
        parser = htmlsax.parser(handler)
        handler.parser = parser
        if self.charset:
            parser.encoding = self.charset
        # parse
        try:
            parser.feed(self.get_content())
            parser.flush()
        except linkparse.StopParse, msg:
            log.debug(LOG_CHECK, "Stopped parsing: %s", msg)
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        if handler.title:
            self.title = handler.title

    def is_parseable (self):
        """
        Return True iff content of this url is parseable.
        """
        return False

    def is_html (self):
        """
        Return True iff content of this url is HTML formatted.
        """
        return False

    def is_css (self):
        """Return True iff content of this url is CSS stylesheet."""
        return False

    def is_http (self):
        """
        Return True for http:// URLs.
        """
        return False

    def is_file (self):
        """
        Return True for file:// URLs.
        """
        return False

    def is_local(self):
        """Return True for local (ie. file://) URLs."""
        return self.is_file()

    def add_warning (self, s, tag=None):
        """
        Add a warning string.
        """
        item = (tag, s)
        if item not in self.warnings and \
           tag not in self.aggregate.config["ignorewarnings"]:
            self.warnings.append(item)

    def add_info (self, s):
        """
        Add an info string.
        """
        if s not in self.info:
            self.info.append(s)

    def copy_from_cache (self, cache_data):
        """
        Fill attributes from cache data.
        """
        self.url = cache_data["url"]
        self.result = cache_data["result"]
        self.has_result = True
        anchor_changed = (self.anchor != cache_data["anchor"])
        for tag, msg in cache_data["warnings"]:
            # do not copy anchor warnings, since the current anchor
            # might have changed
            if anchor_changed and tag == WARN_URL_ANCHOR_NOT_FOUND:
                continue
            self.add_warning(msg, tag=tag)
        for info in cache_data["info"]:
            self.add_info(info)
        self.valid = cache_data["valid"]
        self.dltime = cache_data["dltime"]
        self.dlsize = cache_data["dlsize"]
        self.anchors = cache_data["anchors"]
        self.content_type = cache_data["content_type"]
        self.cached = True
        if anchor_changed and self.valid:
            # recheck anchor
            if self.check_anchor():
                # a new warning has been added - remove cached flag
                self.cached = False

    def get_cache_data (self):
        """Return all data values that should be put in the cache."""
        return {"url": self.url,
                "result": self.result,
                "warnings": self.warnings,
                "info": self.info,
                "valid": self.valid,
                "dltime": self.dltime,
                "dlsize": self.dlsize,
                "anchors": self.anchors,
                "anchor": self.anchor,
                "content_type": self.get_content_type(),
               }

    def get_alias_cache_data (self):
        """Return all data values that should be put in the cache.
        Intended to be overridden by subclasses that handle aliases.
        """
        return self.get_cache_data()

    def set_cache_keys (self):
        """
        Set keys for URL checking and content recursion.
        """
        # remove anchor from content cache key since we assume
        # URLs with different anchors to have the same content
        self.cache_content_key = urlutil.urlunsplit(self.urlparts[:4]+[u''])
        assert isinstance(self.cache_content_key, unicode), self
        log.debug(LOG_CACHE, "Content cache key %r", self.cache_content_key)
        # construct cache key
        self.cache_url_key = self.cache_content_key
        assert isinstance(self.cache_url_key, unicode), self
        log.debug(LOG_CACHE, "URL cache key %r", self.cache_url_key)

    def check_syntax (self):
        """
        Called before self.check(), this function inspects the
        url syntax. Success enables further checking, failure
        immediately logs this url. Syntax checks must not
        use any network resources.
        """
        log.debug(LOG_CHECK, "checking syntax")
        if self.base_url is None:
            self.set_result(_("URL is missing"), valid=False)
            return
        if not (self.base_url or self.parent_url):
            self.set_result(_("URL is empty"), valid=False)
            return
        try:
            self.build_url()
            self.check_url_warnings()
        except tuple(ExcSyntaxList), msg:
            self.set_result(unicode_safe(msg), valid=False)
        else:
            self.set_cache_keys()

    def check_url_warnings(self):
        """Check URL name and length."""
        effectiveurl = urlutil.urlunsplit(self.urlparts)
        if self.url != effectiveurl:
            self.add_warning(_("Effective URL %(url)r.") %
                             {"url": effectiveurl},
                             tag=WARN_URL_EFFECTIVE_URL)
            self.url = effectiveurl
        if len(self.url) > URL_MAX_LENGTH:
            args = dict(len=len(self.url), max=URL_MAX_LENGTH)
            self.set_result(_("URL length %(len)d is longer than maximum of %(max)d.") % args, valid=False)
        elif len(self.url) > URL_WARN_LENGTH:
            args = dict(len=len(self.url), warn=URL_WARN_LENGTH)
            self.add_warning(_("URL length %(len)d is longer than %(warn)d.") % args,
                tag=WARN_URL_TOO_LONG)

    def build_url (self):
        """
        Construct self.url and self.urlparts out of the given base
        url information self.base_url, self.parent_url and self.base_ref.
        """
        # norm base url - can raise UnicodeError from url.idna_encode()
        base_url, is_idn = url_norm(self.base_url, self.encoding)
        # make url absolute
        if self.base_ref:
            # use base reference as parent url
            if ":" not in self.base_ref:
                # some websites have a relative base reference
                self.base_ref = urljoin(self.parent_url, self.base_ref)
            self.url = urljoin(self.base_ref, base_url)
        elif self.parent_url:
            # strip the parent url query and anchor
            urlparts = list(urlparse.urlsplit(self.parent_url))
            urlparts[4] = ""
            parent_url = urlutil.urlunsplit(urlparts)
            self.url = urljoin(parent_url, base_url)
        else:
            self.url = base_url
        # urljoin can unnorm the url path, so norm it again
        urlparts = list(urlparse.urlsplit(self.url))
        if urlparts[2]:
            urlparts[2] = urlutil.collapse_segments(urlparts[2])
        self.url = urlutil.urlunsplit(urlparts)
        # split into (modifiable) list
        self.urlparts = strformat.url_unicode_split(self.url)
        # and unsplit again
        self.url = urlutil.urlunsplit(self.urlparts)
        self.build_url_parts()

    def build_url_parts (self):
        """Set userinfo, host, port and anchor from self.urlparts.
        Also checks for obfuscated IP addresses.
        """
        # check userinfo@host:port syntax
        self.userinfo, host = urllib.splituser(self.urlparts[1])
        # set host lowercase
        if self.userinfo:
            self.urlparts[1] = "%s@%s" % (self.userinfo, host.lower())
        else:
            self.urlparts[1] = host.lower()
        # safe anchor for later checking
        self.anchor = self.urlparts[4]
        port = urlutil.default_ports.get(self.scheme, 0)
        self.host, self.port = urlutil.splitport(host, port=port)
        if self.port is None:
            raise LinkCheckerError(_("URL host %(host)r has invalid port") %
                    {"host": host})
        if self.scheme in scheme_requires_host:
            if not self.host:
                raise LinkCheckerError(_("URL has empty hostname"))
            self.check_obfuscated_ip()

    def check_obfuscated_ip (self):
        """Warn if host of this URL is obfuscated IP address."""
        # check if self.host can be an IP address
        # check for obfuscated IP address
        if iputil.is_obfuscated_ip(self.host):
            ips = iputil.resolve_host(self.host)
            if ips:
                self.add_warning(
                   _("URL %(url)s has obfuscated IP address %(ip)s") % \
                   {"url": self.base_url, "ip": ips.pop()},
                          tag=WARN_URL_OBFUSCATED_IP)

    def check (self):
        """Main check function for checking this URL."""
        if self.aggregate.config["trace"]:
            trace.trace_on()
        try:
            self.local_check()
        except (socket.error, select.error):
            # on Unix, ctrl-c can raise
            # error: (4, 'Interrupted system call')
            etype, value = sys.exc_info()[:2]
            if etype == errno.EINTR:
                raise KeyboardInterrupt(value)
            else:
                raise
        finally:
            # close/release possible open connection
            self.close_connection()

    def add_country_info (self):
        """Try to ask GeoIP database for country info."""
        if self.host:
            country = geoip.get_country(self.host)
            if country:
                self.add_info(_("URL is located in %(country)s.") %
                {"country": _(country)})

    def add_size_info (self):
        """Store size of URL content from meta info into self.size.
        Must be implemented in subclasses."""
        pass

    def local_check (self):
        """Local check function can be overridden in subclasses."""
        log.debug(LOG_CHECK, "Checking %s", self)
        # start time for check
        check_start = time.time()
        # strict extern URLs should not be checked
        assert not self.extern[1], 'checking strict extern URL'
        # check connection
        log.debug(LOG_CHECK, "checking connection")
        try:
            self.check_connection()
            self.add_size_info()
            self.add_country_info()
        except tuple(ExcList):
            value = self.handle_exception()
            # make nicer error msg for unknown hosts
            if isinstance(value, socket.error) and value.args[0] == -2:
                value = _('Hostname not found')
            # make nicer error msg for bad status line
            if isinstance(value, httplib.BadStatusLine):
                value = _('Bad HTTP response %(line)r') % {"line": str(value)}
            self.set_result(unicode_safe(value), valid=False)
        self.checktime = time.time() - check_start
        if self.do_check_content:
            # check content and recursion
            try:
                self.check_content()
                if self.allows_recursion():
                    self.parse_url()
                # check content size
                self.check_size()
            except tuple(ExcList):
                value = self.handle_exception()
                # make nicer error msg for bad status line
                if isinstance(value, httplib.BadStatusLine):
                    value = _('Bad HTTP response %(line)r') % {"line": str(value)}
                self.add_warning(_("could not get content: %(msg)s") %
                     {"msg": str(value)}, tag=WARN_URL_ERROR_GETTING_CONTENT)

    def close_connection (self):
        """
        Close an opened url connection.
        """
        if self.url_connection is None:
            # no connection is open
            return
        try:
            self.url_connection.close()
        except Exception:
            # ignore close errors
            pass
        self.url_connection = None

    def handle_exception (self):
        """
        An exception occurred. Log it and set the cache flag.
        """
        etype, evalue = sys.exc_info()[:2]
        log.debug(LOG_CHECK, "Error in %s: %s %s", self.url, etype, evalue, exception=True)
        # note: etype must be the exact class, not a subclass
        if (etype in ExcNoCacheList) or \
           (etype == socket.error and evalue.args[0]==errno.EBADF) or \
            not evalue:
            # EBADF occurs when operating on an already socket
            self.caching = False
        # format unicode message "<exception name>: <error message>"
        errmsg = unicode(etype.__name__)
        uvalue = strformat.unicode_safe(evalue)
        if uvalue:
            errmsg += u": %s" % uvalue
        # limit length to 240
        return strformat.limit(errmsg, length=240)

    def check_connection (self):
        """
        The basic connection check uses urllib2.urlopen to initialize
        a connection object.
        """
        self.url_connection = urllib2.urlopen(self.url)

    def allows_recursion (self):
        """
        Return True iff we can recurse into the url's content.
        """
        log.debug(LOG_CHECK, "checking recursion of %r ...", self.url)
        # Test self.valid before self.is_parseable().
        if not self.valid:
            log.debug(LOG_CHECK, "... no, invalid.")
            return False
        if not self.is_parseable():
            log.debug(LOG_CHECK, "... no, not parseable.")
            return False
        if not self.can_get_content():
            log.debug(LOG_CHECK, "... no, cannot get content.")
            return False
        rec_level = self.aggregate.config["recursionlevel"]
        if rec_level >= 0 and self.recursion_level >= rec_level:
            log.debug(LOG_CHECK, "... no, maximum recursion level reached.")
            return False
        if self.extern[0]:
            log.debug(LOG_CHECK, "... no, extern.")
            return False
        if not self.content_allows_robots():
            log.debug(LOG_CHECK, "... no, robots.")
            return False
        log.debug(LOG_CHECK, "... yes, recursion.")
        return True

    def content_allows_robots (self):
        """
        Return False if the content of this URL forbids robots to
        search for recursive links.
        """
        if not self.is_html():
            return True
        if not (self.is_http() or self.is_file()):
            return True
        # construct parser object
        handler = linkparse.MetaRobotsFinder()
        parser = htmlsax.parser(handler)
        handler.parser = parser
        if self.charset:
            parser.encoding = self.charset
        # parse
        try:
            parser.feed(self.get_content())
            parser.flush()
        except linkparse.StopParse, msg:
            log.debug(LOG_CHECK, "Stopped parsing: %s", msg)
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        return handler.follow

    def get_anchors (self):
        """Store anchors for this URL. Precondition: this URL is
        an HTML resource."""
        log.debug(LOG_CHECK, "Getting HTML anchors %s", self)
        self.find_links(self.add_anchor, tags=linkparse.AnchorTags)

    def find_links (self, callback, tags=None):
        """Parse into content and search for URLs to check.
        Found URLs are added to the URL queue.
        """
        # construct parser object
        handler = linkparse.LinkFinder(callback, tags=tags)
        parser = htmlsax.parser(handler)
        if self.charset:
            parser.encoding = self.charset
        handler.parser = parser
        # parse
        try:
            parser.feed(self.get_content())
            parser.flush()
        except linkparse.StopParse, msg:
            log.debug(LOG_CHECK, "Stopped parsing: %s", msg)
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None

    def add_anchor (self, url, line, column, name, base):
        """Add anchor URL."""
        self.anchors.append((url, line, column, name, base))

    def check_anchor (self):
        """If URL is valid, parseable and has an anchor, check it.
        A warning is logged and True is returned if the anchor is not found.
        """
        if not (self.anchor and self.aggregate.config["anchors"] and
                self.valid and self.is_html()):
            return
        log.debug(LOG_CHECK, "checking anchor %r in %s", self.anchor, self.anchors)
        enc = lambda anchor: urlutil.url_quote_part(anchor, encoding=self.encoding)
        if any(x for x in self.anchors if enc(x[0]) == self.anchor):
            return
        if self.anchors:
            anchornames = sorted(set(u"`%s'" % x[0] for x in self.anchors))
            anchors = u", ".join(anchornames)
        else:
            anchors = u"-"
        args = {"name": self.anchor, "anchors": anchors}
        msg = u"%s %s" % (_("Anchor `%(name)s' not found.") % args,
                          _("Available anchors: %(anchors)s.") % args)
        self.add_warning(msg, tag=WARN_URL_ANCHOR_NOT_FOUND)
        return True

    def set_extern (self, url):
        """
        Match URL against extern and intern link patterns. If no pattern
        matches the URL is extern. Sets self.extern to a tuple (bool,
        bool) with content (is_extern, is_strict).

        @return: None
        """
        if self.extern:
            return
        if not url:
            self.extern = (1, 1)
            return
        for entry in self.aggregate.config["externlinks"]:
            match = entry['pattern'].search(url)
            if (entry['negate'] and not match) or \
               (match and not entry['negate']):
                log.debug(LOG_CHECK, "Extern URL %r", url)
                self.extern = (1, entry['strict'])
                return
        for entry in self.aggregate.config["internlinks"]:
            match = entry['pattern'].search(url)
            if (entry['negate'] and not match) or \
               (match and not entry['negate']):
                log.debug(LOG_CHECK, "Intern URL %r", url)
                self.extern = (0, 0)
                return
        log.debug(LOG_CHECK, "Explicit extern URL %r", url)
        self.extern = (1, 0)
        return

    def get_content_type (self):
        """Return content MIME type or empty string.
        Should be overridden in subclasses."""
        if self.content_type is None:
            self.content_type = u""
        return self.content_type

    def can_get_content (self):
        """Indicate wether url get_content() can be called."""
        return True

    def get_content (self):
        """Precondition: url_connection is an opened URL."""
        if self.data is None:
            log.debug(LOG_CHECK, "Get content of %r", self.url)
            t = time.time()
            self.data, self.dlsize = self.read_content()
            self.dltime = time.time() - t
        return self.data

    def read_content (self):
        """Return data and data size for this URL.
        Can be overridden in subclasses."""
        if self.size > self.MaxFilesizeBytes:
            raise LinkCheckerError(_("File size too large"))
        data = self.url_connection.read(self.MaxFilesizeBytes+1)
        if len(data) > self.MaxFilesizeBytes:
            raise LinkCheckerError(_("File size too large"))
        if not self.is_local():
            urls = self.aggregate.add_download_data(self.cache_content_key, data)
            self.warn_duplicate_content(urls)
        return data, len(data)

    def warn_duplicate_content(self, urls):
        """If given URL list is not empty, warn about duplicate URL content.
        @param urls: URLs with duplicate content
        @ptype urls: list of unicode
        """
        if not urls or self.size <= 0:
            return
        if urlutil.is_duplicate_content_url(self.url, urls[0]):
            return
        args = dict(
            urls=u",".join(urls),
            size=_(" with %s") % strformat.strsize(self.size),
        )
        self.add_warning(_("Content%(size)s is the same as in URLs (%(urls)s).") % args, tag=WARN_URL_CONTENT_DUPLICATE)

    def check_content (self):
        """Check content data for warnings, syntax errors, viruses etc."""
        if not (self.valid and self.can_get_content()):
            return
        if self.is_html():
            self.set_title_from_content()
            if self.aggregate.config["anchors"]:
                self.get_anchors()
        self.check_anchor()
        self.check_warningregex()
        # is it an intern URL?
        if not self.extern[0]:
            # check HTML/CSS syntax
            if self.aggregate.config["checkhtml"] and self.is_html():
                self.check_html()
            if self.aggregate.config["checkcss"] and self.is_css():
                self.check_css()
            # check with clamav
            if self.aggregate.config["scanvirus"]:
                self.scan_virus()

    def check_warningregex (self):
        """Check if content matches a given regular expression."""
        config = self.aggregate.config
        warningregex = config["warningregex"]
        if not (warningregex and self.valid and self.is_parseable()):
            return
        log.debug(LOG_CHECK, "checking content for warning regex")
        try:
            content = self.get_content()
            curpos = 0
            curline = 1
            # add warnings for found matches, up to the maximum allowed number
            for num, match in enumerate(warningregex.finditer(content)):
                # calculate line number for match
                curline += content.count('\n', curpos, match.start())
                curpos = match.start()
                # add a warning message
                msg = _("Found %(match)r at line %(line)d in link contents.")
                self.add_warning(msg %
                   {"match": match.group(), "line": curline},
                   tag=WARN_URL_WARNREGEX_FOUND)
                # check for maximum number of warnings
                if num >= config["warningregex_max"]:
                    break
        except tuple(ExcList):
            value = self.handle_exception()
            self.set_result(unicode_safe(value), valid=False)

    def check_size (self):
        """Check content size if it is zero or larger than a given
        maximum size.
        """
        if self.dlsize == 0:
            self.add_warning(_("Content size is zero."),
                             tag=WARN_URL_CONTENT_SIZE_ZERO)
        else:
            maxbytes = self.aggregate.config["warnsizebytes"]
            if maxbytes is not None and self.dlsize >= maxbytes:
                self.add_warning(
                   _("Content size %(dlsize)s is larger than %(maxbytes)s.") %
                        {"dlsize": strformat.strsize(self.dlsize),
                         "maxbytes": strformat.strsize(maxbytes)},
                          tag=WARN_URL_CONTENT_SIZE_TOO_LARGE)
        if self.size != -1 and self.dlsize != -1 and self.dlsize != self.size:
                self.add_warning(_("Download size (%(dlsize)d Byte) "
                        "does not equal content size (%(size)d Byte).") %
                        {"dlsize": self.dlsize,
                         "size": self.size},
                          tag=WARN_URL_CONTENT_SIZE_UNEQUAL)

    def check_html (self):
        """Check HTML syntax of this page (which is supposed to be HTML)
        with the local HTML tidy module."""
        if not fileutil.has_module("tidy"):
            return self.check_html_w3()
        import tidy
        options = dict(output_html=0, show_warnings=1, quiet=True,
            input_encoding='utf8', output_encoding='utf8', tidy_mark=0)
        try:
            doc = tidy.parseString(self.get_content(), **options)
            errors = filter_tidy_errors(doc.errors)
            if errors:
                for err in errors:
                    self.add_warning(u"HTMLTidy: %s" % err)
            else:
                self.add_info(u"HTMLTidy: %s" % _("valid HTML syntax"))
        except Exception:
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("tidy HTML parsing caused error: %(msg)s ") %
                {"msg": err})

    def check_css (self):
        """Check CSS syntax of this page (which is supposed to be CSS)
        with the local cssutils module."""
        if not fileutil.has_module("cssutils"):
            return self.check_css_w3()
        import cssutils
        try:
            csslog = logging.getLogger('cssutils')
            csslog.propagate = 0
            del csslog.handlers[:]
            handler = StoringHandler()
            csslog.addHandler(handler)
            csslog.setLevel(logging.WARN)
            cssparser = cssutils.CSSParser(log=csslog)
            cssparser.parseString(self.get_content(), href=self.url)
            if handler.storage:
                for record in handler.storage:
                    self.add_warning(u"cssutils: %s" % record.getMessage())
            else:
                self.add_info(u"cssutils: %s" % _("valid CSS syntax"))
        except Exception:
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("cssutils parsing caused error: %(msg)s") %
                {"msg": err})

    def check_w3_errors (self, xml, w3type):
        """Add warnings for W3C HTML or CSS errors in xml format.
        w3type is either "W3C HTML" or "W3C CSS"."""
        from xml.dom.minidom import parseString
        dom = parseString(xml)
        for error in dom.getElementsByTagName('m:error'):
            warnmsg = _("%(w3type)s validation error at line %(line)s col %(column)s: %(msg)s")
            attrs = {
                "w3type": w3type,
                "line": getXmlText(error, "m:line"),
                "column": getXmlText(error, "m:col"),
                "msg": getXmlText(error, "m:message"),
            }
            self.add_warning(warnmsg % attrs)

    def check_html_w3 (self):
        """Check HTML syntax of this page (which is supposed to be HTML)
        with the online W3C HTML validator documented at
        http://validator.w3.org/docs/api.html
        """
        self.aggregate.check_w3_time()
        try:
            u = urllib2.urlopen('http://validator.w3.org/check',
                urllib.urlencode({
                    'fragment': self.get_content(),
                    'output': 'soap12',
                }))
            if u.headers.get('x-w3c-validator-status', 'Invalid') == 'Valid':
                self.add_info(u"W3C Validator: %s" % _("valid HTML syntax"))
                return
            self.check_w3_errors(u.read(), "W3C HTML")
        except Exception:
            raise
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("HTML W3C validation caused error: %(msg)s ") %
                {"msg": err})

    def check_css_w3 (self):
        """Check CSS syntax of this page (which is supposed to be CSS)
        with the online W3C CSS validator documented at
        http://jigsaw.w3.org/css-validator/manual.html#expert
        """
        self.aggregate.check_w3_time()
        try:
            host = 'jigsaw.w3.org'
            path = '/css-validator/validator'
            params = {
                'text': "div {}",
                'warning': '2',
                'output': 'soap12',
            }
            fields = params.items()
            content_type, body = httputil.encode_multipart_formdata(fields)
            h = httplib.HTTPConnection(host)
            h.putrequest('POST', path)
            h.putheader('Content-Type', content_type)
            h.putheader('Content-Length', str(len(body)))
            h.endheaders()
            h.send(body)
            r = h.getresponse(True)
            if r.getheader('X-W3C-Validator-Status', 'Invalid') == 'Valid':
                self.add_info(u"W3C Validator: %s" % _("valid CSS syntax"))
                return
            self.check_w3_errors(r.read(), "W3C HTML")
        except Exception:
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("CSS W3C validation caused error: %(msg)s ") %
                {"msg": err})

    def scan_virus (self):
        """Scan content for viruses."""
        infected, errors = clamav.scan(self.get_content())
        for msg in infected:
            self.add_warning(u"Virus scan infection: %s" % msg)
        for msg in errors:
            self.add_warning(u"Virus scan error: %s" % msg)

    def parse_url (self):
        """
        Parse url content and search for recursive links.
        Default parse type is html.
        """
        self.parse_html()
        self.add_num_url_info()

    def get_user_password (self):
        """Get tuple (user, password) from configured authentication.
        Both user and password can be None.
        """
        if self.userinfo:
            # URL itself has authentication info
            return urllib.splitpasswd(self.userinfo)
        return self.aggregate.config.get_user_password(self.url)

    def parse_html (self):
        """Parse into HTML content and search for URLs to check.
        Found URLs are added to the URL queue.
        """
        log.debug(LOG_CHECK, "Parsing HTML %s", self)
        self.find_links(self.add_url)

    def add_url (self, url, line=0, column=0, name=u"", base=None):
        """Queue URL data for checking."""
        self.num_urls += 1
        if base:
            base_ref = urlutil.url_norm(base)[0]
        else:
            base_ref = None
        url_data = get_url_from(url, self.recursion_level+1, self.aggregate,
            parent_url=self.url, base_ref=base_ref, line=line, column=column,
            name=name, parent_content_type=self.content_type)
        if url_data.has_result or not url_data.extern[1]:
            # Only queue URLs which have a result or are not strict extern.
            self.aggregate.urlqueue.put(url_data)

    def add_num_url_info(self):
        """Add number of URLs parsed to info."""
        if self.num_urls > 0:
            attrs = {"num": self.num_urls}
            msg = _n("%(num)d URL parsed.", "%(num)d URLs parsed.", self.num_urls)
            self.add_info(msg % attrs)

    def parse_opera (self):
        """Parse an opera bookmark file."""
        log.debug(LOG_CHECK, "Parsing Opera bookmarks %s", self)
        from ..bookmarks.opera import parse_bookmark_data
        for url, name, lineno in parse_bookmark_data(self.get_content()):
            self.add_url(url, line=lineno, name=name)

    def parse_chromium (self):
        """Parse a Chromium or Google Chrome bookmark file."""
        log.debug(LOG_CHECK, "Parsing Chromium bookmarks %s", self)
        from ..bookmarks.chromium import parse_bookmark_data
        for url, name in parse_bookmark_data(self.get_content()):
            self.add_url(url, name=name)

    def parse_safari (self):
        """Parse a Safari bookmark file."""
        log.debug(LOG_CHECK, "Parsing Safari bookmarks %s", self)
        from ..bookmarks.safari import parse_bookmark_data
        for url, name in parse_bookmark_data(self.get_content()):
            self.add_url(url, name=name)

    def parse_text (self):
        """Parse a text file with one url per line; comment and blank
        lines are ignored."""
        log.debug(LOG_CHECK, "Parsing text %s", self)
        lineno = 0
        for line in self.get_content().splitlines():
            lineno += 1
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            self.add_url(line, line=lineno)

    def parse_css (self):
        """
        Parse a CSS file for url() patterns.
        """
        log.debug(LOG_CHECK, "Parsing CSS %s", self)
        lineno = 0
        linkfinder = linkparse.css_url_re.finditer
        strip_comments = linkparse.strip_c_comments
        for line in strip_comments(self.get_content()).splitlines():
            lineno += 1
            for mo in linkfinder(line):
                column = mo.start("url")
                url = strformat.unquote(mo.group("url").strip())
                self.add_url(url, line=lineno, column=column)

    def parse_swf (self):
        """Parse a SWF file for URLs."""
        linkfinder = linkparse.swf_url_re.finditer
        for mo in linkfinder(self.get_content()):
            url = mo.group()
            self.add_url(url)

    def parse_word (self):
        """Parse a word file for hyperlinks."""
        if not winutil.has_word():
            return
        filename = self.get_temp_filename()
        # open word file and parse hyperlinks
        try:
            app = winutil.get_word_app()
            try:
                doc = winutil.open_wordfile(app, filename)
                try:
                    for link in doc.Hyperlinks:
                        self.add_url(link.Address, name=link.TextToDisplay)
                finally:
                    winutil.close_wordfile(doc)
            finally:
                winutil.close_word_app(app)
        except winutil.Error, msg:
            log.warn(LOG_CHECK, "Error parsing word file: %s", msg)

    def parse_wml (self):
        """Parse into WML content and search for URLs to check.
        Found URLs are added to the URL queue.
        """
        log.debug(LOG_CHECK, "Parsing WML %s", self)
        self.find_links(self.add_url, tags=linkparse.WmlTags)

    def get_temp_filename (self):
        """Get temporary filename for content to parse."""
        # store content in temporary file
        fd, filename = fileutil.get_temp_file(mode='wb', suffix='.doc',
            prefix='lc_')
        try:
            fd.write(self.get_content())
        finally:
            fd.close()
        return filename

    def serialized (self):
        """
        Return serialized url check data as unicode string.
        """
        sep = unicode_safe(os.linesep)
        if self.base_url is not None:
            assert isinstance(self.base_url, unicode), self
        if self.parent_url is not None:
            assert isinstance(self.parent_url, unicode), self
        if self.base_ref is not None:
            assert isinstance(self.base_ref, unicode), self
        assert isinstance(self.name, unicode), self
        return sep.join([
            u"%s link" % self.scheme,
            u"base_url=%r" % self.base_url,
            u"parent_url=%r" % self.parent_url,
            u"base_ref=%r" % self.base_ref,
            u"recursion_level=%s" % self.recursion_level,
            u"url_connection=%s" % self.url_connection,
            u"line=%d" % self.line,
            u"column=%d" % self.column,
            u"name=%r" % self.name,
            u"anchor=%r" % self.anchor,
            u"cached=%s" % self.cached,
            u"cache_key=%s" % self.cache_url_key,
           ])

    def get_intern_pattern (self, url=None):
        """Get pattern for intern URL matching.

        @param url: the URL to set intern pattern for, else self.url
        @ptype url: unicode or None
        @return non-empty regex pattern or None
        @rtype String or None
        """
        return None

    def add_intern_pattern(self, url=None):
        """Add intern URL regex to config."""
        try:
            pat = self.get_intern_pattern(url=url)
            if pat:
                log.debug(LOG_CHECK, "Add intern pattern %r", pat)
                self.aggregate.config['internlinks'].append(get_link_pat(pat))
        except UnicodeError, msg:
            res = _("URL has unparsable domain name: %(domain)s") % \
                {"domain": msg}
            self.set_result(res, valid=False)

    def __str__ (self):
        """
        Get URL info.

        @return: URL info, encoded with the output logger encoding
        @rtype: string
        """
        s = self.serialized()
        return self.aggregate.config['logger'].encode(s)

    def __repr__ (self):
        """
        Get URL info.

        @return: URL info
        @rtype: unicode
        """
        return u"<%s >" % self.serialized()

    def to_wire_dict (self):
        """Return a simplified transport object for logging.

        The transport object must contain these attributes:
        - url_data.valid: bool
          Indicates if URL is valid
        - url_data.cached: bool
          Indicates if URL data has been loaded from cache.
        - url_data.result: unicode
          Result string
        - url_data.warnings: list of tuples (tag, warning message)
          List of tagged warnings for this URL.
        - url_data.name: unicode string or None
          name of URL (eg. filename or link name)
        - url_data.parent_url: unicode or None
          Parent URL
        - url_data.base_ref: unicode
          HTML base reference URL of parent
        - url_data.url: unicode
          Fully qualified URL.
        - url_data.domain: unicode
          URL domain part.
        - url_data.checktime: int
          Number of seconds needed to check this link, default: zero.
        - url_data.dltime: int
          Number of seconds needed to download URL content, default: -1
        - url_data.dlsize: int
          Size of downloaded URL content, default: -1
        - url_data.info: list of unicode
          Additional information about this URL.
        - url_data.line: int
          Line number of this URL at parent document, or -1
        - url_data.column: int
          Column number of this URL at parent document, or -1
        - url_data.cache_url_key: unicode
          Cache key for this URL.
        - url_data.content_type: unicode
          MIME content type for URL content.
        - url_data.level: int
          Recursion level until reaching this URL from start URL
        - url_data.last_modified: datetime
          Last modification date of retrieved page (or None).
        """
        return dict(valid=self.valid,
          extern=self.extern[0],
          cached=self.cached,
          result=self.result,
          warnings=self.warnings[:],
          name=self.name or u"",
          title=self.get_title(),
          parent_url=self.parent_url or u"",
          base_ref=self.base_ref or u"",
          base_url=self.base_url or u"",
          url=self.url or u"",
          domain=(self.urlparts[1] if self.urlparts else u""),
          checktime=self.checktime,
          dltime=self.dltime,
          dlsize=self.dlsize,
          info=self.info,
          line=self.line,
          column=self.column,
          cache_url_key=self.cache_url_key,
          content_type=self.get_content_type(),
          level=self.recursion_level,
          modified=self.modified,
        )

    def to_wire (self):
        """Return compact UrlData object with information from to_wire_dict().
        """
        return CompactUrlData(self.to_wire_dict())


def filter_tidy_errors (errors):
    """Filter certain errors from HTML tidy run."""
    return [x for x in errors if not \
        (x.severity=='W' and x.message=='<table> lacks "summary" attribute')]


urlDataAttr = [
    'valid',
    'extern',
    'cached',
    'result',
    'warnings',
    'name',
    'title',
    'parent_url',
    'base_ref',
    'base_url',
    'url',
    'domain',
    'checktime',
    'dltime',
    'dlsize',
    'info',
    'modified',
    'line',
    'column',
    'cache_url_key',
    'content_type',
    'level',
]

class CompactUrlData (object):
    """Store selected UrlData attributes in slots to minimize memory usage."""
    __slots__ = urlDataAttr

    def __init__(self, wired_url_data):
        '''Set all attributes according to the dictionnary wired_url_data'''
        for attr in urlDataAttr:
            setattr(self, attr, wired_url_data[attr])
