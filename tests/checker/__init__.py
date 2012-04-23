# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2011 Bastian Kleineidam
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
Define standard test support classes funtional for LinkChecker tests.
"""
import os
import re
import codecs
import difflib
import unittest
import linkcheck.checker
import linkcheck.configuration
import linkcheck.director
import linkcheck.logger
from .. import get_file

# helper alias
get_url_from = linkcheck.checker.get_url_from


class TestLogger (linkcheck.logger.Logger):
    """
    Output logger for automatic regression tests.
    """

    def __init__ (self, **kwargs):
        """
        The kwargs must have "expected" keyword with the expected logger
        output lines.
        """
        super(TestLogger, self).__init__(**kwargs)
        # list of expected output lines
        self.expected = kwargs['expected']
        # list of real output lines
        self.result = []
        # diff between expected and real output
        self.diff = []

    def start_output (self):
        """
        Nothing to do here.
        """
        pass

    def log_url (self, url_data):
        """
        Append logger output to self.result.
        """
        if self.has_part('url'):
            url = u"url %s" % url_data.base_url
            if url_data.cached:
                url += u" (cached)"
            self.result.append(url)
        if self.has_part('cachekey'):
            self.result.append(u"cache key %s" % url_data.cache_url_key)
        if self.has_part('realurl'):
            self.result.append(u"real url %s" % url_data.url)
        if self.has_part('name') and url_data.name:
            self.result.append(u"name %s" % url_data.name)
        if self.has_part('base') and url_data.base_ref:
            self.result.append(u"baseurl %s" % url_data.base_ref)
        if self.has_part('info'):
            for info in url_data.info:
                if "Last modified" not in info and \
                   "is located in" not in info:
                    self.result.append(u"info %s" % info)
        if self.has_part('warning'):
            for tag, warning in url_data.warnings:
                self.result.append(u"warning %s" % warning)
        if self.has_part('result'):
            self.result.append(u"valid" if url_data.valid else u"error")
        # note: do not append url_data.result since this is
        # platform dependent

    def end_output (self, linknumber=-1):
        """
        Stores differences between expected and result in self.diff.
        """
        for line in difflib.unified_diff(self.expected, self.result):
            if not isinstance(line, unicode):
                # The ---, +++ and @@ lines from diff format are ascii encoded.
                # Make them unicode.
                line = unicode(line, "ascii", "replace")
            self.diff.append(line)


def get_file_url (filename):
    return re.sub("^([a-zA-Z]):", r"/\1|", filename.replace("\\", "/"))


def add_fileoutput_config (config):
    if os.name == 'posix':
        devnull = '/dev/null'
    elif os.name == 'nt':
        devnull = 'NUL'
    else:
        return
    for ftype in linkcheck.logger.Loggers.keys():
        if ftype in ('test', 'blacklist'):
            continue
        logger = config.logger_new(ftype, fileoutput=1, filename=devnull)
        config['fileoutput'].append(logger)


def get_test_aggregate (confargs, logargs):
    """Initialize a test configuration object."""
    config = linkcheck.configuration.Configuration()
    config.logger_add('test', TestLogger)
    config['recursionlevel'] = 1
    config['logger'] = config.logger_new('test', **logargs)
    add_fileoutput_config(config)
    # uncomment for debugging
    #config.init_logging(None, debug=["all"])
    config["anchors"] = True
    config["verbose"] = True
    config["complete"] = True
    config['threads'] = 0
    config['status'] = False
    config['cookies'] = True
    config.update(confargs)
    return linkcheck.director.get_aggregate(config)


class LinkCheckTest (unittest.TestCase):
    """
    Functional test class with ability to test local files.
    """

    def setUp (self):
        """Ensure the current locale setting is the default.
        Otherwise, warnings will get translated and will break tests."""
        super(LinkCheckTest, self).setUp()
        linkcheck.init_i18n(loc='C')

    def norm (self, url, encoding=None):
        """Helper function to norm a url."""
        return linkcheck.url.url_norm(url, encoding=encoding)[0]

    def get_attrs (self, **kwargs):
        """Return current and data directory as dictionary.
        You can augment the dict with keyword attributes."""
        d = {
            'curdir': get_file_url(os.getcwd()),
            'datadir': "tests/checker/data",
        }
        d.update(kwargs)
        return d

    def get_resultlines (self, filename):
        """
        Return contents of file, as list of lines without line endings,
        ignoring empty lines and lines starting with a hash sign (#).
        """
        resultfile = get_file(u"%s.result" % filename)
        d = {'curdir': get_file_url(os.getcwd()),
             'datadir': get_file_url(get_file()),
            }
        # the webserver uses the first free port number
        if hasattr(self, 'port'):
            d['port'] = self.port
        # all result files are encoded in utf-8
        with codecs.open(resultfile, "r", "utf-8") as f:
            return [line.rstrip(u'\r\n') % d for line in f
                    if line.strip() and not line.startswith(u'#')]

    def file_test (self, filename, confargs=None):
        """Check <filename> with expected result in <filename>.result."""
        url = get_file(filename)
        if confargs is None:
            confargs = {}
        logargs = {'expected': self.get_resultlines(filename)}
        aggregate = get_test_aggregate(confargs, logargs)
        url_data = get_url_from(url, 0, aggregate)
        linkcheck.add_intern_pattern(url_data, aggregate.config)
        aggregate.urlqueue.put(url_data)
        linkcheck.director.check_urls(aggregate)
        diff = aggregate.config['logger'].diff
        if diff:
            msg = unicode(os.linesep).join([url] + diff)
            self.fail_unicode(msg)

    def fail_unicode (self, msg):
        """Print encoded fail message."""
        # XXX self.fail() only supports ascii
        self.fail(msg.encode("ascii", "replace"))

    def direct (self, url, resultlines, parts=None, recursionlevel=0,
                confargs=None):
        """Check url with expected result."""
        assert isinstance(url, unicode), repr(url)
        if confargs is None:
            confargs = {'recursionlevel': recursionlevel}
        else:
            confargs['recursionlevel'] = recursionlevel
        logargs = {'expected': resultlines}
        if parts is not None:
            logargs['parts'] = parts
        aggregate = get_test_aggregate(confargs, logargs)
        # initial URL has recursion level zero
        url_reclevel = 0
        url_data = get_url_from(url, url_reclevel, aggregate)
        linkcheck.add_intern_pattern(url_data, aggregate.config)
        aggregate.urlqueue.put(url_data)
        linkcheck.director.check_urls(aggregate)
        diff = aggregate.config['logger'].diff
        if diff:
            l = [u"Differences found testing %s" % url]
            l.extend(x.rstrip() for x in diff[2:])
            self.fail_unicode(unicode(os.linesep).join(l))
