# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2005  Bastian Kleineidam
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
Define standard test support classes funtional for LinkChecker tests.
"""

import os
import codecs
import unittest
import difflib

import linkcheck
linkcheck.init_i18n()
import linkcheck.checker
import linkcheck.checker.cache
import linkcheck.checker.consumer
import linkcheck.configuration
import linkcheck.logger


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

    def new_url (self, url_data):
        """
        Append logger output to self.result.
        """
        if self.has_field('url'):
            url = u"url %s" % url_data.base_url
            if url_data.cached:
                url += u" (cached)"
            self.result.append(url)
        if self.has_field('cachekey'):
            self.result.append(u"cache key %s" % url_data.cache_url_key)
        if self.has_field('realurl'):
            self.result.append(u"real url %s" % url_data.url)
        if self.has_field('name') and url_data.name:
            self.result.append(u"name %s" % url_data.name)
        if self.has_field('base') and url_data.base_ref:
            self.result.append(u"baseurl %s" % url_data.base_ref)
        if self.has_field('info'):
            for info in url_data.info:
                self.result.append(u"info %s" % info)
        if self.has_field('warning'):
            for warning in url_data.warning:
                self.result.append(u"warning %s" % warning)
        if self.has_field('result'):
            self.result.append(url_data.valid and u"valid" or u"error")
        # note: do not append url_data.result since this is
        # platform dependent

    def end_output (self, linknumber=-1):
        """
        Stores differences between expected and result in self.diff.
        """
        for line in difflib.unified_diff(self.expected, self.result):
            if not isinstance(line, unicode):
                line = unicode(line, "iso8859-1", "ignore")
            self.diff.append(line)


def get_test_consumer (confargs, logargs):
    """
    Initialize a test configuration object.
    """
    config = linkcheck.configuration.Configuration()
    config.logger_add('test', TestLogger)
    config['recursionlevel'] = 1
    config['logger'] = config.logger_new('test', **logargs)
    config["anchors"] = True
    config["verbose"] = True
    config['threads'] = 0
    config.update(confargs)
    cache = linkcheck.checker.cache.Cache()
    return linkcheck.checker.consumer.Consumer(config, cache)


class StandardTest (unittest.TestCase):
    """
    Functional test class with ability to test local files.
    """

    def setUp (self):
        """
        Check resources, using the provided function check_resources()
        from test.py.
        """
        super(StandardTest, self).setUp()
        if hasattr(self, "needed_resources"):
            self.check_resources(self.needed_resources)

    def norm (self, url):
        """
        Helper function to norm a url.
        """
        return linkcheck.url.url_norm(url)[0]

    def get_file (self, filename):
        """
        Get file name located within 'data' directory.
        """
        return unicode(os.path.join("linkcheck", "ftests", "data", filename))

    def get_resultlines (self, filename):
        """
        Return contents of file, as list of lines without line endings,
        ignoring empty lines and lines starting with a hash sign (#).
        """
        resultfile = self.get_file(filename+".result")
        d = {'curdir': os.getcwd()}
        f = codecs.open(resultfile, "r", "iso8859-1")
        resultlines = [line.rstrip() % d for line in f \
                       if line.strip() and not line.startswith(u'#')]
        f.close()
        return resultlines

    def file_test (self, filename, confargs=None):
        """
        Check <filename> with expected result in <filename>.result.
        """
        url = self.get_file(filename)
        if confargs is None:
            confargs = {}
        logargs = {'expected': self.get_resultlines(filename)}
        consumer = get_test_consumer(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(
                                      url, 0, consumer, cmdline=True)
        consumer.append_url(url_data)
        linkcheck.checker.check_urls(consumer)
        if consumer.config['logger'].diff:
            sep = unicode(os.linesep)
            l = [url] + consumer.config['logger'].diff
            l = sep.join(l)
            self.fail(l.encode("iso8859-1", "ignore"))

    def direct (self, url, resultlines, fields=None, recursionlevel=0,
                confargs=None):
        """
        Check url with expected result.
        """
        assert isinstance(url, unicode), repr(url)
        if confargs is None:
            confargs = {'recursionlevel': recursionlevel}
        else:
            confargs['recursionlevel'] = recursionlevel
        logargs = {'expected': resultlines}
        if fields is not None:
            logargs['fields'] = fields
        consumer = get_test_consumer(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(url, 0, consumer)
        consumer.append_url(url_data)
        linkcheck.checker.check_urls(consumer)
        if consumer.config['logger'].diff:
            sep = unicode(os.linesep)
            l = [url] + consumer.config['logger'].diff
            l = sep.join(l)
            self.fail(l.encode("iso8859-1", "ignore"))
