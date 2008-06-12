# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2008 Bastian Kleineidam
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
import traceback

from . import absolute_url, StoringHandler, get_url_from
from ..cache import geoip
from .. import (log, LOG_CHECK, LOG_CACHE, httputil, httplib2 as httplib,
    strformat, containers, LinkCheckerError, url as urlutil,
    trace, clamav)
from ..HtmlParser import htmlsax
from ..htmlutil import linkparse, titleparse
from .const import (WARN_URL_EFFECTIVE_URL, WARN_URL_UNICODE_DOMAIN,
    WARN_URL_UNNORMED, WARN_URL_ERROR_GETTING_CONTENT,
    WARN_URL_ANCHOR_NOT_FOUND, WARN_URL_WARNREGEX_FOUND,
    WARN_URL_CONTENT_TOO_LARGE, ExcList, ExcSyntaxList, ExcNoCacheList)

# helper alias
unicode_safe = strformat.unicode_safe

def urljoin (parent, url, scheme):
    """
    If url is relative, join parent and url. Else leave url as-is.

    @return joined url
    """
    if url.startswith(scheme+":"):
        return url
    return urlparse.urljoin(parent, url)


def url_norm (url):
    """
    Wrapper for url.url_norm() to convert UnicodeError in LinkCheckerError.
    """
    try:
        return urlutil.url_norm(url)
    except UnicodeError:
        msg = _("URL has unparsable domain name: %(name)s") % \
            {"name": sys.exc_info()[1]}
        raise LinkCheckerError(msg)


class UrlBase (object):
    """An URL with additional information like validity etc."""

    def __init__ (self, base_url, recursion_level, aggregate,
                  parent_url = None, base_ref = None,
                  line = -1, column = -1, name = u""):
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
        """
        self.init(base_ref, base_url, parent_url, recursion_level,
                  aggregate, line, column, name)
        self.reset()
        self.check_syntax()


    def init (self, base_ref, base_url, parent_url, recursion_level,
              aggregate, line, column, name):
        """
        Initialize internal data.
        """
        self.base_ref = base_ref
        # note that self.base_url must not be modified
        self.base_url = base_url
        self.parent_url = parent_url
        self.recursion_level = recursion_level
        self.aggregate = aggregate
        self.line = line
        self.column = column
        self.name = name
        if self.base_ref:
            assert not urlutil.url_needs_quoting(self.base_ref), \
                   "unquoted base reference URL %r" % self.base_ref
        if self.parent_url:
            assert not urlutil.url_needs_quoting(self.parent_url), \
                   "unquoted parent URL %r" % self.parent_url
        url = absolute_url(base_url, base_ref, parent_url)
        # assume file link if no scheme is found
        self.scheme = url.split(":", 1)[0] or "file"
        # warn if URL is redirected (for commandline client)
        self.warn_redirect = False

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
        # the anchor part of url
        self.anchor = None
        # the result message string and flag
        self.result = u""
        self.has_result = False
        # cached or not
        self.cached = False
        # valid or not
        self.valid = True
        # list of warnings (without duplicates)
        self.warnings = containers.SetList()
        # list of infos (without duplicates)
        self.info = containers.SetList()
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
        # extern flags (is_extern, is_strict), both enabled as default
        self.extern = (1, 1)
        # flag if the result should be cached
        self.caching = True
        # title is either the URL or parsed from content
        self.title = None

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
            url = self.url if self.url else self.base_url
            self.title = url
            if "/" in url:
                title = url.rsplit("/", 1)[1]
                if title:
                    self.title = title
        return self.title

    def set_title_from_content (self):
        """Set title of page the URL refers to.from page content."""
        if self.valid and self.is_html():
            try:
                handler = titleparse.TitleFinder(self.get_content())
            except tuple(ExcList):
                return
            parser = htmlsax.parser(handler)
            handler.parser = parser
            # parse
            parser.feed(self.get_content())
            parser.flush()
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

    def add_warning (self, s, tag=None):
        """
        Add a warning string.
        """
        self.warnings.append((tag, s))

    def add_info (self, s, tag=None):
        """
        Add an info string.
        """
        self.info.append((tag, s))

    def copy_from_cache (self, cache_data):
        """
        Fill attributes from cache data.
        """
        self.result = cache_data["result"]
        self.has_result = True
        self.warnings.extend(cache_data["warnings"])
        self.info.extend(cache_data["info"])
        self.valid = cache_data["valid"]
        self.dltime = cache_data["dltime"]
        self.dlsize = cache_data["dlsize"]
        self.cached = True

    def get_cache_data (self):
        """
        Return all data values that should be put in the cache.
        """
        return {"result": self.result,
                "warnings": self.warnings,
                "info": self.info,
                "valid": self.valid,
                "dltime": self.dltime,
                "dlsize": self.dlsize,
               }

    def get_alias_cache_data (self):
        """
        Return all data values that should be put in the cache.
        Intended to be overridden by subclasses that handle aliases.
        """
        return self.get_cache_data()

    def set_cache_keys (self):
        """
        Set keys for URL checking and content recursion.
        """
        # remove anchor from content cache key since we assume
        # URLs with different anchors to have the same content
        self.cache_content_key = urlparse.urlunsplit(self.urlparts[:4]+[u''])
        assert isinstance(self.cache_content_key, unicode), self
        log.debug(LOG_CACHE, "Content cache key %r", self.cache_content_key)
        # construct cache key
        if self.aggregate.config["anchorcaching"] and \
           self.aggregate.config["anchors"]:
            # do not ignore anchor
            parts = self.urlparts[:]
            parts[4] = self.anchor
            self.cache_url_key = urlparse.urlunsplit(parts)
        else:
            # no anchor caching
            self.cache_url_key = self.cache_content_key
        assert isinstance(self.cache_url_key, unicode), self
        log.debug(LOG_CACHE, "URL cache key %r", self.cache_url_key)

    def check_syntax (self):
        """
        Called before self.check(), this function inspects the
        url syntax. Success enables further checking, failure
        immediately logs this url. Syntax checks must not
        use any network resources.

        @return: True if syntax is correct, else False.
        @rtype: bool
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
            # check url warnings
            effectiveurl = urlparse.urlunsplit(self.urlparts)
            if self.url != effectiveurl:
                self.add_warning(_("Effective URL %(url)r.") %
                                 {"url": effectiveurl},
                                 tag=WARN_URL_EFFECTIVE_URL)
                self.url = effectiveurl
        except tuple(ExcSyntaxList), msg:
            self.set_result(unicode_safe(msg), valid=False)
            return
        self.set_cache_keys()

    def build_url (self):
        """
        Construct self.url and self.urlparts out of the given base
        url information self.base_url, self.parent_url and self.base_ref.
        """
        # norm base url - can raise UnicodeError from url.idna_encode()
        base_url, is_idn = url_norm(self.base_url)
        if is_idn:
            self.add_warning(_("""URL %(url)r has a unicode domain name which
                          is not yet widely supported. You should use
                          the URL %(idna_url)r instead.""") % \
                          {"url": self.base_url, "idna_url": base_url},
                          tag=WARN_URL_UNICODE_DOMAIN)
        elif self.base_url != base_url:
            self.add_warning(
              _("Base URL is not properly normed. Normed URL is %(url)s.") %
               {'url': base_url}, tag=WARN_URL_UNNORMED)
        # make url absolute
        if self.base_ref:
            # use base reference as parent url
            if ":" not in self.base_ref:
                # some websites have a relative base reference
                self.base_ref = urljoin(self.parent_url, self.base_ref,
                                        self.scheme)
            self.url = urljoin(self.base_ref, base_url, self.scheme)
        elif self.parent_url:
            # strip the parent url query and anchor
            urlparts = list(urlparse.urlsplit(self.parent_url))
            urlparts[3] = urlparts[4] = ""
            parent_url = urlparse.urlunsplit(urlparts)
            self.url = urljoin(parent_url, base_url, self.scheme)
        else:
            self.url = base_url
        # note: urljoin can unnorm the url path, so norm it again
        urlparts = list(urlparse.urlsplit(self.url))
        if urlparts[2]:
            urlparts[2] = urlutil.collapse_segments(urlparts[2])
        self.url = urlparse.urlunsplit(urlparts)
        # split into (modifiable) list
        self.urlparts = strformat.url_unicode_split(self.url)
        # and unsplit again
        self.url = urlparse.urlunsplit(self.urlparts)
        # check userinfo@host:port syntax
        self.userinfo, host = urllib.splituser(self.urlparts[1])
        # set host lowercase
        if self.userinfo:
            self.urlparts[1] = "%s@%s" % (self.userinfo, host.lower())
        else:
            self.urlparts[1] = host.lower()
        # safe anchor for later checking
        self.anchor = self.urlparts[4]
        self.host, self.port = urllib.splitport(host)
        if self.port is not None:
            if not urlutil.is_numeric_port(self.port):
                raise LinkCheckerError(_("URL has invalid port %(port)r") %
                    {"port": str(self.port)})
            self.port = int(self.port)

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
        """
        Try to ask GeoIP database for country info.
        """
        country = geoip.get_country(self.host)
        if country is not None:
            self.add_info(_("URL is located in %(country)s.") %
                {"country": _(country)})

    def local_check (self):
        """Local check function can be overridden in subclasses."""
        log.debug(LOG_CHECK, "Checking %s", self)
        # start time for check
        check_start = time.time()
        self.set_extern(self.url)
        if self.extern[0] and self.extern[1]:
            self.add_info(_("Outside of domain filter, checked only syntax."))
            return

        # check connection
        log.debug(LOG_CHECK, "checking connection")
        try:
            self.check_connection()
            self.add_country_info()
            if self.aggregate.config["anchors"]:
                self.check_anchors()
        except tuple(ExcList):
            value = self.handle_exception()
            # make nicer error msg for unknown hosts
            if isinstance(value, socket.error) and value[0] == -2:
                value = _('Hostname not found')
            # make nicer error msg for bad status line
            if isinstance(value, httplib.BadStatusLine):
                value = _('Bad HTTP response %(line)r') % {"line": str(value)}
            self.set_result(unicode_safe(value), valid=False)
        if self.can_get_content():
            self.set_title_from_content()
            self.check_content()
        self.checktime = time.time() - check_start
        # check recursion
        try:
            if self.allows_recursion():
                self.parse_url()
            # check content size
            self.check_size()
        except tuple(ExcList):
            value = self.handle_exception()
            self.add_warning(_("could not get content: %(msg)r") %
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
        etype, value, tb = sys.exc_info()
        log.debug(LOG_CHECK, "exception %s", traceback.format_tb(tb))
        # note: etype must be the exact class, not a subclass
        if (etype in ExcNoCacheList) or \
           (etype == socket.error and value[0]==errno.EBADF) or \
            not value:
            # EBADF occurs when operating on an already socket
            self.caching = False
        errmsg = etype.__name__
        if str(value):
            # use Exception class name
            errmsg += ": %s" % str(value)
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
        if  rec_level >= 0 and self.recursion_level >= rec_level:
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
        Return True if the content of this URL forbids robots to
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
        # parse
        parser.feed(self.get_content())
        parser.flush()
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        return handler.follow

    def check_anchors (self):
        """
        If URL was valid and a HTML resource, check the anchors and
        log a warning when an anchor was not found.
        """
        if not (self.valid and self.anchor and self.is_html() and \
                self.can_get_content()):
            # do not bother
            return
        log.debug(LOG_CHECK, "checking anchor %r", self.anchor)
        handler = linkparse.LinkFinder(self.get_content(),
                                   tags={'a': [u'name'], None: [u'id']})
        parser = htmlsax.parser(handler)
        handler.parser = parser
        # parse
        parser.feed(self.get_content())
        parser.flush()
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        if any(x for x in handler.urls if x[0] == self.anchor):
            return
        self.add_warning(_("Anchor #%(name)s not found.") %
            {"name": self.anchor}, tag=WARN_URL_ANCHOR_NOT_FOUND)

    def set_extern (self, url):
        """
        Match URL against extern and intern link patterns. If no pattern
        matches the URL is extern. Sets self.extern to a tuple (bool,
        bool) with content (is_extern, is_strict).

        @return: None
        """
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

    def can_get_content (self):
        """
        Indicate wether url get_content() can be called.
        """
        return True

    def get_content (self):
        """
        Precondition: url_connection is an opened URL.
        """
        if self.data is None:
            t = time.time()
            self.data = self.url_connection.read()
            self.dltime = time.time() - t
            self.dlsize = len(self.data)
        return self.data

    def check_content (self):
        """Check content data for warnings, syntax errors, viruses etc."""
        if not (self.can_get_content() and self.valid):
            # no data to check
            return
        warningregex = self.aggregate.config["warningregex"]
        if warningregex:
            log.debug(LOG_CHECK, "checking content")
            try:
                match = warningregex.search(self.get_content())
                if match:
                    self.add_warning(_("Found %(match)r in link contents.") %
                       {"match": match.group()}, tag=WARN_URL_WARNREGEX_FOUND)
            except tuple(ExcList):
                value = self.handle_exception()
                self.set_result(unicode_safe(value), valid=False)
        # is it an intern URL?
        if not self.extern[0]:
            # check HTML/CSS syntax
            if self.aggregate.config["checkhtml"] and self.is_html():
                self.check_html()
            if self.aggregate.config["checkcss"] and self.is_css():
                self.check_css()
            if self.aggregate.config["checkhtmlw3"] and self.is_html():
                self.check_html_w3()
            if self.aggregate.config["checkcssw3"] and self.is_css():
                self.check_css_w3()
            # check with clamav
            if self.aggregate.config["scanvirus"]:
                self.scan_virus()

    def check_size (self):
        """
        If a maximum size was given, call this function to check it
        against the content size of this url.
        """
        maxbytes = self.aggregate.config["warnsizebytes"]
        if maxbytes is not None and self.dlsize >= maxbytes:
            self.add_warning(
                   _("Content size %(dlsize)s is larger than %(maxbytes)s.") %
                        {"dlsize": strformat.strsize(self.dlsize),
                         "maxbytes": strformat.strsize(maxbytes)},
                          tag=WARN_URL_CONTENT_TOO_LARGE)

    def check_html (self):
        """Check HTML syntax of this page (which is supposed to be HTML)
        with the local HTML tidy module."""
        try:
            import tidy
        except ImportError:
            log.warn(LOG_CHECK, _("warning: tidy module is not available; " \
                 "download from http://utidylib.berlios.de/"))
            return
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
                _("warning: tidy HTML parsing caused error: %(msg)s ") %
                {"msg": err})

    def check_css (self):
        """Check CSS syntax of this page (which is supposed to be CSS)
        with the local cssutils module."""
        try:
            import cssutils
        except ImportError:
            log.warn(LOG_CHECK,
                _("warning: cssutils module is not available; " \
                 "download from http://cthedot.de/cssutils/"))
            return
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
                _("warning: cssutils parsing caused error: %(msg)s") %
                {"msg": err})

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
                    'output': 'xml',
                }))
            if u.headers.get('x-w3c-validator-status', 'Invalid') == 'Valid':
                self.add_info(u"W3C Validator: %s" % _("valid HTML syntax"))
                return
            from xml.dom.minidom import parseString
            dom = parseString(u.read())
            elements = dom.getElementsByTagName('messages')[0].getElementsByTagName('msg')
            for msg in [e.firstChild.wholeText for e in elements]:
                self.add_warning(u"W3C HTML validation: %s" % msg)
        except Exception:
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("warning: HTML W3C validation caused error: %(msg)s ") %
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
            r = h.getresponse()
            if r.getheader('X-W3C-Validator-Status', 'Invalid') == 'Valid':
                self.add_info(u"W3C Validator: %s" % _("valid CSS syntax"))
                return
            from xml.dom.minidom import parseString
            dom = parseString(r.read())
            elements = dom.getElementsByTagName('m:errors')[0].getElementsByTagName('m:error')
            for msg in [e.firstChild.wholeText for e in elements]:
                self.add_warning(u"W3C HTML validation: %s" % msg)
        except Exception:
            # catch _all_ exceptions since we dont want third party module
            # errors to propagate into this library
            err = str(sys.exc_info()[1])
            log.warn(LOG_CHECK,
                _("warning: CSS W3C validation caused error: %(msg)s ") %
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

    def get_user_password (self):
        """
        Get tuple (user, password) from configured authentication.
        Both user and password can be None if not specified.
        """
        for auth in self.aggregate.config["authentication"]:
            if auth['pattern'].match(self.url):
                return auth['user'], auth['password']
        return None, None

    def parse_html (self):
        """
        Parse into HTML content and search for URLs to check.
        Found URLs are added to the URL queue.
        """
        log.debug(LOG_CHECK, "Parsing HTML %s", self)
        # construct parser object
        handler = linkparse.LinkFinder(self.get_content())
        parser = htmlsax.parser(handler)
        handler.parser = parser
        # parse
        parser.feed(self.get_content())
        parser.flush()
        # break cyclic dependencies
        handler.parser = None
        parser.handler = None
        for url, line, column, name, codebase in handler.urls:
            if codebase:
                base_ref = codebase
            else:
                base_ref = handler.base_ref
            base_ref = urlutil.url_norm(base_ref)[0]
            url_data = get_url_from(url,
                  self.recursion_level+1, self.aggregate, parent_url=self.url,
                  base_ref=base_ref, line=line, column=column, name=name)
            self.aggregate.urlqueue.put(url_data)

    def parse_opera (self):
        """
        Parse an opera bookmark file.
        """
        log.debug(LOG_CHECK, "Parsing Opera bookmarks %s", self)
        name = ""
        lineno = 0
        for line in self.get_content().splitlines():
            lineno += 1
            line = line.strip()
            if line.startswith("NAME="):
                name = line[5:]
            elif line.startswith("URL="):
                url = line[4:]
                if url:
                    url_data = get_url_from(url, self.recursion_level+1,
                        self.aggregate, parent_url=self.url,
                        line=lineno, name=name)
                    self.aggregate.urlqueue.put(url_data)
                name = ""

    def parse_text (self):
        """
        Parse a text file with on url per line; comment and blank
        lines are ignored.
        """
        log.debug(LOG_CHECK, "Parsing text %s", self)
        lineno = 0
        for line in self.get_content().splitlines():
            lineno += 1
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            url_data = get_url_from(line,
                              self.recursion_level+1, self.aggregate,
                              parent_url=self.url, line=lineno)
            self.aggregate.urlqueue.put(url_data)

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
                url_data = get_url_from(url,
                             self.recursion_level+1, self.aggregate,
                             parent_url=self.url, line=lineno, column=column)
                self.aggregate.urlqueue.put(url_data)

    def parse_swf (self):
        """Parse a SWF file for URLs."""
        linkfinder = linkparse.swf_url_re.finditer
        for mo in linkfinder(self.get_content()):
            url = mo.group()
            url_data = get_url_from(url,
                         self.recursion_level+1, self.aggregate,
                         parent_url=self.url)
            self.aggregate.urlqueue.put(url_data)

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
           ])

    def get_intern_pattern (self):
        """
        Get pattern for intern URL matching.

        @return non-empty regex pattern or None
        @rtype String or None
        """
        return None

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


def filter_tidy_errors (errors):
    """Filter certain errors from HTML tidy run."""
    return [x for x in errors if not \
        (x.severity=='W' and x.message=='<table> lacks "summary" attribute')]
